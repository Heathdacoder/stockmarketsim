import tkinter as tk
from tkinter import ttk, messagebox
import requests
import datetime
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import requests.exceptions # Import for specific error handling

# Just loading the API key from a separate function so it's not hardcoded everywhere.
def load_api_key():
    # Pretend this is coming from a proper secure file – this is just a placeholder.
    return "d3nmgf9r01qo7511n57gd3nmgf9r01qo7511n580" 

API_KEY = load_api_key()
TICKERS = ["AAPL","MSFT","GOOG","TSLA","AMZN","FB","NVDA","JPM","V","DIS",
           "NFLX","ADBE","PYPL","INTC","CSCO","CRM","NKE","BAC","XOM","LMT"]
REFRESH_INTERVAL = 10000  # milliseconds
PORTFOLIO_FILE = "portfolio.json"
HISTORY_FILE = "history.json"
TRANSACTIONS_FILE = "transactions.json" # Stores all the buys + sells

# --- DATA CLASSES ---

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.price = 0
        self.history = []

    # Gets the current price from the API, and if it fails we just keep the old price.
    def fetch_current_price(self):
        url = f"https://finnhub.io/api/v1/quote?symbol={self.symbol}&token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data and data.get("c"):
                self.price = data.get("c", self.price)
        except requests.exceptions.RequestException as e:
            print(f"API Error (fetch_current_price for {self.symbol}): {e}")
            pass

    # Gets about a month of daily historical prices from the API.
    def fetch_historical(self):
        end = int(datetime.datetime.now().timestamp())
        start = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp())
        url = f"https://finnhub.io/api/v1/stock/candle?symbol={self.symbol}&resolution=D&from={start}&to={end}&token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("s")=="ok":
                self.history = [(datetime.datetime.fromtimestamp(ts), price) for ts, price in zip(data["t"], data["c"])]
        except requests.exceptions.RequestException as e:
            print(f"API Error (fetch_historical for {self.symbol}): {e}")
            pass

    # Works out % change over the month.
    def monthly_change(self):
        if self.history and len(self.history) > 0 and self.price > 0:
            old_price = self.history[0][1]
            if old_price != 0:
                return ((self.price - old_price)/old_price)*100
        return 0

class Portfolio:
    def __init__(self):
        self.cash = 100000.0
        self.holdings = {}
        self.avg_price = {}
        self.realised_profit = 0.0
        self.history = []
        self.transaction_log = [] # Every buy/sell gets saved here
        self.load_from_json()
        self.load_history()
        self.load_transactions()

    # Just wraps the original save method.
    def save_to_json(self):
        self.save()

    # Just wraps the original load method.
    def load_from_json(self):
        self.load()

    # Handles buying shares + updating weighted average cost.
    def buy(self, stock, amount):
        cost = stock.price * amount
        
        if amount <= 0:
            return False, "Amount must be a positive number."
        if cost > self.cash:
            return False, f"Not enough cash. Cost: ${cost:,.2f} | Cash: ${self.cash:,.2f}"
        if stock.price <= 0:
            return False, "Cannot buy stock with zero or negative price (API error)."

        self.cash -= cost
        if stock.symbol in self.holdings:
            total_qty = self.holdings[stock.symbol] + amount
            total_cost = self.avg_price[stock.symbol] * self.holdings[stock.symbol] + cost
            self.avg_price[stock.symbol] = total_cost / total_qty
            self.holdings[stock.symbol] += amount
        else:
            self.holdings[stock.symbol] = amount
            self.avg_price[stock.symbol] = stock.price
        
        # Add buy to the transaction log
        self.transaction_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "symbol": stock.symbol, "type": "BUY", "shares": amount,
            "price": stock.price, "total_cost": cost
        })
        self.save_transactions()
        self.save_to_json()
        return True, f"Bought {amount} shares of {stock.symbol}"

    # Handles selling shares + working out profit/loss.
    def sell(self, stock, amount):
        if amount <= 0:
            return False, "Amount must be a positive number."
        if stock.symbol not in self.holdings:
            return False, "You do not own any shares of this stock."
        if self.holdings[stock.symbol] < amount:
            return False, f"Not enough shares. You own: {self.holdings[stock.symbol]}"

        self.realised_profit += (stock.price - self.avg_price[stock.symbol]) * amount
        self.cash += stock.price * amount
        self.holdings[stock.symbol] -= amount
        
        if self.holdings[stock.symbol] == 0:
            del self.holdings[stock.symbol]
            del self.avg_price[stock.symbol]
            
        # Add sell to the transaction log
        self.transaction_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "symbol": stock.symbol, "type": "SELL", "shares": amount,
            "price": stock.price, "realised_pnl": (stock.price - self.avg_price[stock.symbol]) * amount
        })
        self.save_transactions()
        self.save_to_json()
        return True, f"Sold {amount} shares of {stock.symbol}"

    # Works out total portfolio value including cash + all shares.
    def total_value(self, stocks):
        total = self.cash
        for sym, qty in self.holdings.items():
            total += qty * stocks[sym].price
        return total

    # Adds up all unrealised P&L.
    def unrealised_profit(self, stocks):
        profit = 0
        for sym, qty in self.holdings.items():
            if sym in self.avg_price:
                profit += (stocks[sym].price - self.avg_price[sym]) * qty
        return profit

    # Saves current portfolio value to the history list.
    def record_history(self, stocks):
        self.history.append((datetime.datetime.now(), self.total_value(stocks)))
        self.save_history()

    # Saves portfolio data.
    def save(self):
        data = {
            "cash": self.cash,
            "holdings": self.holdings,
            "avg_price": self.avg_price,
            "realised_profit": self.realised_profit
        }
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # Loads portfolio data and checks if file is broken.
    def load(self):
        if os.path.exists(PORTFOLIO_FILE):
            try:
                with open(PORTFOLIO_FILE, "r") as f:
                    data = json.load(f)
                    self.cash = data.get("cash", 100000)
                    self.holdings = data.get("holdings", {})
                    self.avg_price = data.get("avg_price", {})
                    self.realised_profit = data.get("realised_profit", 0)
            except json.JSONDecodeError:
                print(f"Error: {PORTFOLIO_FILE} is corrupted. Starting fresh.")
                pass

    # Saves the portfolio value history.
    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump([(dt.isoformat(), val) for dt, val in self.history], f, indent=4)

    # Loads the portfolio value history + checks for corrupted files.
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    self.history = [(datetime.datetime.fromisoformat(dt), val) for dt, val in json.load(f)]
            except (json.JSONDecodeError, ValueError):
                print(f"Error: {HISTORY_FILE} is corrupted. Starting fresh.")
                self.history = []
                
    # Saves the buy/sell logs.
    def save_transactions(self):
        with open(TRANSACTIONS_FILE, "w") as f:
            json.dump(self.transaction_log, f, indent=4)

    # Loads the buy/sell logs and checks they're readable.
    def load_transactions(self):
        if os.path.exists(TRANSACTIONS_FILE):
            try:
                with open(TRANSACTIONS_FILE, "r") as f:
                    self.transaction_log = json.load(f)
            except (json.JSONDecodeError, ValueError):
                print(f"Error: {TRANSACTIONS_FILE} is corrupted. Starting fresh.")
                self.transaction_log = []

# --- GUI CLASSES ---

class PortfolioWindow(tk.Toplevel):
    # This is your original portfolio window.
    def __init__(self,parent,stocks,portfolio):
        super().__init__(parent)
        self.title("Portfolio Overview")
        self.geometry("1000x700")
        self.configure(bg="#1e1e2e")
        self.stocks = stocks
        self.portfolio = portfolio
        self.create_widgets()

    def create_widgets(self):
        pnl_frame = tk.Frame(self,bg="#1e1e2e")
        pnl_frame.pack(fill="x",pady=15)
        
        total_val = self.portfolio.total_value(self.stocks)
        unrealised = self.portfolio.unrealised_profit(self.stocks)
        realised = self.portfolio.realised_profit
        
        tk.Label(pnl_frame,text=f"Total Value: ${total_val:,.2f}",bg="#1e1e2e",fg="gold",font=("Consolas",14, "bold")).pack(side="left",padx=30)
        tk.Label(pnl_frame,text=f"Unrealised P&L: ${unrealised:,.2f}",bg="#1e1e2e",fg="orange",font=("Consolas",14)).pack(side="left",padx=30)
        tk.Label(pnl_frame,text=f"Realised P&L: ${realised:,.2f}",bg="#1e1e2e",fg="lime",font=("Consolas",14)).pack(side="right",padx=30)

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(9,4),dpi=100)
        if self.portfolio.history:
            times, values = zip(*self.portfolio.history)
            ax.plot(times,values,color="lime",marker="o",linewidth=2)
            ax.set_title("Portfolio Value Over Time",fontsize=14)
            ax.set_xlabel("Date/Time")
            ax.set_ylabel("Total Value ($)")
            ax.grid(True, linestyle="--", alpha=0.5)
        else:
            ax.text(0.5,0.5,"No history yet.",ha="center",va="center",color="gray",fontsize=14)
        
        fig.patch.set_facecolor('#1e1e2e')
        ax.set_facecolor('#2a2a40')
            
        canvas = FigureCanvasTkAgg(fig,self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both",expand=True,padx=20,pady=20)
        NavigationToolbar2Tk(canvas,self).update()

class TransactionWindow(tk.Toplevel):
    # Shows every buy/sell the user has ever made.
    def __init__(self, parent, portfolio):
        super().__init__(parent)
        self.title("Transaction History")
        self.geometry("1000x600")
        self.configure(bg="#1e1e2e")
        self.portfolio = portfolio
        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self, bg="#1e1e2e", padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Trans.Treeview", background="#2a2a40", foreground="white", rowheight=28, fieldbackground="#2a2a40")
        style.map("Trans.Treeview", background=[('selected', '#5e81ac')])
        
        self.table = ttk.Treeview(frame, columns=("Timestamp", "Type", "Symbol", "Shares", "Price", "P/L / Cost"), 
                                  show="headings", style="Trans.Treeview")
        
        self.table.heading("Timestamp", text="Date/Time")
        self.table.heading("Type", text="Type")
        self.table.heading("Symbol", text="Symbol")
        self.table.heading("Shares", text="Shares")
        self.table.heading("Price", text="Price ($)")
        self.table.heading("P/L / Cost", text="P&L / Cost ($)")
        
        self.table.column("Timestamp", width=180, anchor="w")
        self.table.column("Type", width=80, anchor="center")
        self.table.column("Symbol", width=80, anchor="center")
        self.table.column("Shares", width=80, anchor="center")
        self.table.column("Price", width=120, anchor="e")
        self.table.column("P/L / Cost", width=120, anchor="e")
        
        self.table.pack(fill="both", expand=True)
        self.load_transactions()

    # Adds rows to the table.
    def load_transactions(self):
        for row in self.table.get_children():
            self.table.delete(row)
        
        for log in reversed(self.portfolio.transaction_log):
            timestamp = datetime.datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            tx_type = log["type"]
            symbol = log["symbol"]
            shares = log["shares"]
            price = f"{log['price']:.2f}"
            
            if tx_type == "SELL":
                pnl = f"{log['realised_pnl']:,.2f}"
                tag = 'green' if log['realised_pnl'] >= 0 else 'red'
            else:
                pnl = f"({log['total_cost']:,.2f})"
                tag = 'blue'
                
            self.table.insert("", "end", values=(timestamp, tx_type, symbol, shares, price, pnl), tags=(tag,))

        self.table.tag_configure('green', foreground='lime')
        self.table.tag_configure('red', foreground='red')
        self.table.tag_configure('blue', foreground='cyan')

class StockApp:
    # This is the main app window.
    def __init__(self, root):
        self.root = root
        self.stocks = {sym: Stock(sym) for sym in TICKERS}
        self.portfolio = Portfolio()
        root.title("Stock Market Simulator")
        root.geometry("1200x800")
        root.configure(bg="#1e1e2e")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e2e", foreground="white", font=("Segoe UI",12))
        style.configure("TButton", font=("Segoe UI",11,"bold"), padding=8, relief="flat", background="#5e81ac", foreground="white")
        style.configure("Treeview", background="#2a2a40", foreground="white", rowheight=28, fieldbackground="#2a2a40")
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), background="#3b4252", foreground="white")
        style.map("TButton", background=[('active', '#81a1c1')])

        control = tk.Frame(root,bg="#1e1e2e")
        control.pack(pady=15)
        self.stock_choice = tk.StringVar(value=TICKERS[0])
        self.stock_menu = ttk.Combobox(control,textvariable=self.stock_choice,values=TICKERS,state="readonly",font=("Segoe UI",12), width=10)
        self.stock_menu.grid(row=0,column=0,padx=10)
        self.amount_entry = tk.Entry(control,font=("Segoe UI",12),justify="center",width=12, bg="#3b4252", fg="white", insertbackground="white")
        self.amount_entry.grid(row=0,column=1,padx=10)
        ttk.Button(control,text="Buy",command=self.buy_stock).grid(row=0,column=2,padx=10)
        ttk.Button(control,text="Sell",command=self.sell_stock).grid(row=0,column=3,padx=10)
        ttk.Button(control,text="Stock Graph",command=self.show_graph).grid(row=0,column=4,padx=10)
        ttk.Button(control,text="Portfolio",command=self.open_portfolio_window).grid(row=0,column=5,padx=10)
        ttk.Button(control,text="Txn Log",command=self.open_transaction_window).grid(row=0,column=6,padx=10)
        ttk.Button(control,text="Restart",command=self.restart_portfolio).grid(row=0,column=7,padx=10)

        dash = tk.Frame(root,bg="#1e1e2e")
        dash.pack(fill="both",expand=True,padx=20,pady=20)

        stock_frame = tk.LabelFrame(dash,text="Stock Prices",bg="#1e1e2e",fg="white",font=("Segoe UI",13,"bold"))
        stock_frame.pack(side="left",fill="both",expand=True,padx=10)
        self.stock_table = ttk.Treeview(stock_frame,columns=("Symbol","Price","Monthly"),show="headings",height=18)
        self.stock_table.heading("Symbol",text="Symbol")
        self.stock_table.heading("Price",text="Price ($)")
        self.stock_table.heading("Monthly",text="% Change (30d)")
        self.stock_table.column("Symbol",anchor="center",width=100)
        self.stock_table.column("Price",anchor="e",width=120)
        self.stock_table.column("Monthly",anchor="e",width=120)
        self.stock_table.pack(fill="both",expand=True,padx=5,pady=5)
        self.stock_table.tag_configure('green', foreground='lime')
        self.stock_table.tag_configure('red', foreground='red')

        port_frame = tk.LabelFrame(dash,text="Portfolio",bg="#1e1e2e",fg="white",font=("Segoe UI",13,"bold"))
        port_frame.pack(side="right",fill="both",expand=True,padx=10)
        self.portfolio_table = ttk.Treeview(port_frame,columns=("Symbol","Shares", "AvgCost", "Unrealised"),show="headings",height=18)
        self.portfolio_table.heading("Symbol",text="Symbol")
        self.portfolio_table.heading("Shares",text="Shares Owned")
        self.portfolio_table.heading("AvgCost", text="Avg Cost ($)")
        self.portfolio_table.heading("Unrealised", text="Unrealised P&L ($)")
        self.portfolio_table.column("Symbol",anchor="center",width=100)
        self.portfolio_table.column("Shares",anchor="center",width=120)
        self.portfolio_table.column("AvgCost", anchor="e", width=120)
        self.portfolio_table.column("Unrealised", anchor="e", width=140)
        self.portfolio_table.pack(fill="both",expand=True,padx=5,pady=5)
        self.portfolio_table.tag_configure('green', foreground='lime')
        self.portfolio_table.tag_configure('red', foreground='red')

        self.summary = tk.Label(root,text="",font=("Consolas",15,"bold"),bg="#11111b",fg="white",anchor="center",pady=12)
        self.summary.pack(fill="x",padx=20,pady=10)

        self.update_data(initial_fetch=True)
        self.root.after(REFRESH_INTERVAL,self.auto_refresh)

    def buy_stock(self):
        sym = self.stock_choice.get()
        stock = self.stocks[sym]
        try:
            amount = int(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error","Enter a valid number")
            return
        
        success, message = self.portfolio.buy(stock,amount)
        
        if success:
            messagebox.showinfo("Bought", message)
        else:
            messagebox.showerror("Error", message)
        self.update_display()

    def sell_stock(self):
        sym = self.stock_choice.get()
        stock = self.stocks[sym]
        try:
            amount = int(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error","Enter a valid number")
            return
        
        success, message = self.portfolio.sell(stock,amount)

        if success:
            messagebox.showinfo("Sold", message)
        else:
            messagebox.showerror("Error", message)
        self.update_display()

    # Opens a window that shows the historical price graph.
    def show_graph(self):
        sym = self.stock_choice.get()
        stock = self.stocks[sym]
        win = tk.Toplevel(self.root)
        win.title(f"{sym} Price Chart")
        win.geometry("900x600")
        win.configure(bg="#1e1e2e")
        stock.fetch_historical()
        
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(9,5),dpi=100)
        if stock.history:
            times, prices = zip(*stock.history)
            ax.plot(times,prices,marker="o",color="cyan",linewidth=2)
            change = stock.monthly_change()
            ax.set_title(f"{sym} Price Over Time ({change:+.2f}%)", fontsize=14, color='white')
        else:
            ax.set_title(f"{sym} Price Over Time", fontsize=14, color='white')
            
        ax.set_xlabel("Date/Time", color="gray")
        ax.set_ylabel("Price ($)", color="gray")
        ax.grid(True,linestyle="--",alpha=0.5)
        fig.patch.set_facecolor('#1e1e2e')
        ax.set_facecolor('#2a2a40')
        
        canvas = FigureCanvasTkAgg(fig,win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both",expand=True)
        NavigationToolbar2Tk(canvas,win).update()

    def open_portfolio_window(self):
        self.portfolio.record_history(self.stocks)
        PortfolioWindow(self.root,self.stocks,self.portfolio)

    def open_transaction_window(self):
        TransactionWindow(self.root, self.portfolio)

    def restart_portfolio(self):
        confirm = messagebox.askyesno("Restart","Are you sure you want to reset your entire portfolio? This will delete all saved data.")
        if confirm:
            for f in [PORTFOLIO_FILE, HISTORY_FILE, TRANSACTIONS_FILE]:
                if os.path.exists(f): 
                    try:
                        os.remove(f)
                    except OSError as e:
                        print(f"Error removing file {f}: {e}")

            self.portfolio = Portfolio()
            self.update_display()
            messagebox.showinfo("Restarted", "Portfolio has been reset to $100,000 cash.")

    # Fetches the latest prices (only fetches historical on first load).
    def update_data(self, initial_fetch=False):
        for stock in self.stocks.values():
            stock.fetch_current_price()
            if initial_fetch:
                stock.fetch_historical()
        
        if initial_fetch and self.stocks["AAPL"].price == 0.0:
             messagebox.showwarning("API Warning", "Could not fetch initial live data. Check your API key or network connection.")
             
        self.update_display()

    # Updates all tables + the summary bar.
    def update_display(self):
        for row in self.stock_table.get_children():
            self.stock_table.delete(row)
        for sym, stock in self.stocks.items():
            change = stock.monthly_change()
            tag = 'green' if change >= 0 else 'red'
            self.stock_table.insert("", "end", values=(sym, f"${stock.price:.2f}", f"{change:+.2f}%"), tags=(tag,))
        
        for row in self.portfolio_table.get_children():
            self.portfolio_table.delete(row)
            
        unrealised_total = 0.0
        for sym, shares in self.portfolio.holdings.items():
            avg_cost = self.portfolio.avg_price.get(sym, 0)
            current_price = self.stocks[sym].price
            unrealised_pnl = (current_price - avg_cost) * shares
            unrealised_total += unrealised_pnl
            tag = 'green' if unrealised_pnl >= 0 else 'red'
            
            self.portfolio_table.insert("", "end", 
                                        values=(sym, shares, f"${avg_cost:.2f}", f"{unrealised_pnl:,.2f}"), 
                                        tags=(tag,))

        total_val = self.portfolio.total_value(self.stocks)
        self.summary.config(text=f"Cash: ${self.portfolio.cash:,.2f} | Holdings: ${total_val - self.portfolio.cash:,.2f} | Total Value: ${total_val:,.2f} | Unrealised: ${unrealised_total:,.2f} | Realised: ${self.portfolio.realised_profit:,.2f}")

    def auto_refresh(self):
        self.update_data()
        self.root.after(REFRESH_INTERVAL,self.auto_refresh)

if __name__=="__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()

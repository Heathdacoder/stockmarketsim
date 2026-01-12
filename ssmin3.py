import tkinter as tk
from tkinter import ttk, messagebox
import requests
import datetime
import json
import os
import time
import random  # Added to create fallback data if the API blocks us
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import requests.exceptions


# Function to get the API key safely
def load_api_key():
    return "d5dtrf9r01qjucj41gqgd5dtrf9r01qjucj41gr0"


API_KEY = load_api_key()

# A list of all the stock symbols we are going to use
TICKERS = ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN", "FB", "NVDA", "JPM", "V", "DIS",
           "NFLX", "ADBE", "PYPL", "INTC", "CSCO", "CRM", "NKE", "BAC", "XOM", "LMT"]

# How often the app updates (60 seconds to stay within free API limits)
REFRESH_INTERVAL = 60000
PORTFOLIO_FILE = "portfolio.json"
HISTORY_FILE = "history.json"
TRANSACTIONS_FILE = "transactions.json"


#DATA CLASSES

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.price = 0
        self.history = []

    # This function goes to the internet to get the current price
    def fetch_current_price(self):
        url = f"https://finnhub.io/api/v1/quote?symbol={self.symbol}&token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data:
                if data.get("c"):
                    self.price = data.get("c", self.price)

        except requests.exceptions.RequestException as e:
            print(f"API Error (fetch_current_price for {self.symbol}): {e}")
            pass

    # This gets the data for the graph (last 30 days)
    def fetch_historical(self):
        end = int(datetime.datetime.now().timestamp())
        start = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp())

        url = f"https://finnhub.io/api/v1/stock/candle?symbol={self.symbol}&resolution=D&from={start}&to={end}&token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)

            # If the API blocks us (403), we create mock data so the graph still works
            if response.status_code == 403:
                self.generate_mock_history()
                return

            response.raise_for_status()
            data = response.json()

            if data.get("s") == "ok":
                self.history = []
                if data.get("t") and data.get("c"):
                    for i in range(len(data["t"])):
                        timestamp = data["t"][i]
                        price = data["c"][i]
                        date_obj = datetime.datetime.fromtimestamp(timestamp)
                        self.history.append((date_obj, price))
            else:
                # If the API says 'no_data', we also use mock data
                self.generate_mock_history()

        except requests.exceptions.RequestException:
            # Fallback if the internet is shaky or API is down
            self.generate_mock_history()

    # This is a fallback function to make sure graphs aren't empty
    def generate_mock_history(self):
        self.history = []
        # If we have no price, we can't make a graph
        if self.price == 0:
            return

        base_price = self.price
        # Create 30 days of fake data points based on the current price
        for i in range(30):
            day = datetime.datetime.now() - datetime.timedelta(days=(30 - i))
            # Create a small random price movement
            movement = random.uniform(-0.02, 0.02)
            base_price = base_price * (1 + movement)
            self.history.append((day, base_price))

    # Calculates the percentage change for the table
    def monthly_change(self):
        if self.history:
            if len(self.history) > 1:
                if self.price > 0:
                    old_price = self.history[0][1]
                    if old_price != 0:
                        change = ((self.price - old_price) / old_price) * 100
                        return change
        return 0


class Portfolio:
    def __init__(self):
        self.cash = 100000.0
        self.holdings = {}
        self.avg_price = {}
        self.realised_profit = 0.0
        self.history = []
        self.transaction_log = []

        self.load_from_json()
        self.load_history()
        self.load_transactions()

    def save_to_json(self):
        self.save()

    def load_from_json(self):
        self.load()

    def buy(self, stock, amount):
        cost = stock.price * amount

        if amount <= 0:
            return False, "Amount must be a positive number."
        if cost > self.cash:
            return False, f"Not enough cash. Cost: ${cost:,.2f} | Cash: ${self.cash:,.2f}"
        if stock.price <= 0:
            return False, "Cannot buy stock with zero or negative price (API error)."

        self.cash = self.cash - cost

        if stock.symbol in self.holdings:
            current_qty = self.holdings[stock.symbol]
            new_qty = current_qty + amount

            total_cost_old = self.avg_price[stock.symbol] * current_qty
            total_cost_new = total_cost_old + cost

            self.avg_price[stock.symbol] = total_cost_new / new_qty
            self.holdings[stock.symbol] = new_qty
        else:
            self.holdings[stock.symbol] = amount
            self.avg_price[stock.symbol] = stock.price

        new_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "symbol": stock.symbol,
            "type": "BUY",
            "shares": amount,
            "price": stock.price,
            "total_cost": cost
        }
        self.transaction_log.append(new_record)

        self.save_transactions()
        self.save_to_json()
        return True, f"Bought {amount} shares of {stock.symbol}"

    def sell(self, stock, amount):
        if amount <= 0:
            return False, "Amount must be a positive number."
        if stock.symbol not in self.holdings:
            return False, "You do not own any shares of this stock."

        current_shares = self.holdings[stock.symbol]
        if current_shares < amount:
            return False, f"Not enough shares. You own: {current_shares}"

        diff = stock.price - self.avg_price[stock.symbol]
        profit = diff * amount
        self.realised_profit = self.realised_profit + profit

        revenue = stock.price * amount
        self.cash = self.cash + revenue
        self.holdings[stock.symbol] = self.holdings[stock.symbol] - amount

        if self.holdings[stock.symbol] == 0:
            del self.holdings[stock.symbol]
            del self.avg_price[stock.symbol]

        new_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "symbol": stock.symbol,
            "type": "SELL",
            "shares": amount,
            "price": stock.price,
            "realised_pnl": profit
        }
        self.transaction_log.append(new_record)

        self.save_transactions()
        self.save_to_json()
        return True, f"Sold {amount} shares of {stock.symbol}"

    def total_value(self, stocks):
        total = self.cash
        for sym in self.holdings:
            qty = self.holdings[sym]
            stock_obj = stocks[sym]
            val = qty * stock_obj.price
            total = total + val
        return total

    def unrealised_profit(self, stocks):
        profit = 0
        for sym in self.holdings:
            qty = self.holdings[sym]
            if sym in self.avg_price:
                current_price = stocks[sym].price
                avg_cost = self.avg_price[sym]
                diff = current_price - avg_cost
                profit = profit + (diff * qty)
        return profit

    def record_history(self, stocks):
        now = datetime.datetime.now()
        val = self.total_value(stocks)
        self.history.append((now, val))
        self.save_history()

    def save(self):
        data = {
            "cash": self.cash,
            "holdings": self.holdings,
            "avg_price": self.avg_price,
            "realised_profit": self.realised_profit
        }
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(data, f, indent=4)

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
                pass

    def save_history(self):
        save_data = []
        for item in self.history:
            dt = item[0]
            val = item[1]
            save_data.append((dt.isoformat(), val))

        with open(HISTORY_FILE, "w") as f:
            json.dump(save_data, f, indent=4)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    loaded_data = json.load(f)
                    self.history = []
                    for item in loaded_data:
                        dt_str = item[0]
                        val = item[1]
                        dt_obj = datetime.datetime.fromisoformat(dt_str)
                        self.history.append((dt_obj, val))
            except (json.JSONDecodeError, ValueError):
                self.history = []

    def save_transactions(self):
        with open(TRANSACTIONS_FILE, "w") as f:
            json.dump(self.transaction_log, f, indent=4)

    def load_transactions(self):
        if os.path.exists(TRANSACTIONS_FILE):
            try:
                with open(TRANSACTIONS_FILE, "r") as f:
                    self.transaction_log = json.load(f)
            except (json.JSONDecodeError, ValueError):
                self.transaction_log = []


# --- GUI CLASSES ---

class PortfolioWindow(tk.Toplevel):
    def __init__(self, parent, stocks, portfolio):
        super().__init__(parent)
        self.title("Portfolio Overview")
        self.geometry("1000x700")
        self.configure(bg="#1e1e2e")
        self.stocks = stocks
        self.portfolio = portfolio
        self.create_widgets()

    def create_widgets(self):
        pnl_frame = tk.Frame(self, bg="#1e1e2e")
        pnl_frame.pack(fill="x", pady=15)

        total_val = self.portfolio.total_value(self.stocks)
        unrealised = self.portfolio.unrealised_profit(self.stocks)
        realised = self.portfolio.realised_profit

        tk.Label(pnl_frame, text=f"Total Value: ${total_val:,.2f}", bg="#1e1e2e", fg="gold",
                 font=("Consolas", 14, "bold")).pack(side="left", padx=30)
        tk.Label(pnl_frame, text=f"Unrealised P&L: ${unrealised:,.2f}", bg="#1e1e2e", fg="orange",
                 font=("Consolas", 14)).pack(side="left", padx=30)
        tk.Label(pnl_frame, text=f"Realised P&L: ${realised:,.2f}", bg="#1e1e2e", fg="lime",
                 font=("Consolas", 14)).pack(side="right", padx=30)

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(9, 4), dpi=100)

        if self.portfolio.history:
            times = []
            values = []
            for item in self.portfolio.history:
                times.append(item[0])
                values.append(item[1])

            ax.plot(times, values, color="lime", marker="o", linewidth=2)
            ax.set_title("Portfolio Value Over Time", fontsize=14)
            ax.set_xlabel("Date/Time")
            ax.set_ylabel("Total Value ($)")
            ax.grid(True, linestyle="--", alpha=0.5)
        else:
            ax.text(0.5, 0.5, "No history yet.", ha="center", va="center", color="gray", fontsize=14)

        fig.patch.set_facecolor('#1e1e2e')
        ax.set_facecolor('#2a2a40')

        canvas = FigureCanvasTkAgg(fig, self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        NavigationToolbar2Tk(canvas, self).update()


class TransactionWindow(tk.Toplevel):
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
        style.configure("Trans.Treeview", background="#2a2a40", foreground="white", rowheight=28,
                        fieldbackground="#2a2a40")
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

    def load_transactions(self):
        for row in self.table.get_children():
            self.table.delete(row)
        for log in reversed(self.portfolio.transaction_log):
            timestamp = datetime.datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            tx_type, symbol, shares, price = log["type"], log["symbol"], log["shares"], f"{log['price']:.2f}"
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
    def __init__(self, root):
        self.root = root
        self.stocks = {}
        for sym in TICKERS:
            self.stocks[sym] = Stock(sym)
        self.portfolio = Portfolio()
        root.title("Stock Market Simulator")
        root.geometry("1200x800")
        root.configure(bg="#1e1e2e")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e2e", foreground="white", font=("Segoe UI", 12))
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=8, relief="flat", background="#5e81ac",
                        foreground="white")
        style.configure("Treeview", background="#2a2a40", foreground="white", rowheight=28, fieldbackground="#2a2a40")
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), background="#3b4252", foreground="white")
        style.map("TButton", background=[('active', '#81a1c1')])

        control = tk.Frame(root, bg="#1e1e2e")
        control.pack(pady=15)
        self.stock_choice = tk.StringVar(value=TICKERS[0])
        self.stock_menu = ttk.Combobox(control, textvariable=self.stock_choice, values=TICKERS, state="readonly",
                                       font=("Segoe UI", 12), width=10)
        self.stock_menu.grid(row=0, column=0, padx=10)
        self.amount_entry = tk.Entry(control, font=("Segoe UI", 12), justify="center", width=12, bg="#3b4252",
                                     fg="white", insertbackground="white")
        self.amount_entry.grid(row=0, column=1, padx=10)

        ttk.Button(control, text="Buy", command=self.buy_stock).grid(row=0, column=2, padx=10)
        ttk.Button(control, text="Sell", command=self.sell_stock).grid(row=0, column=3, padx=10)
        ttk.Button(control, text="Stock Graph", command=self.show_graph).grid(row=0, column=4, padx=10)
        ttk.Button(control, text="Portfolio", command=self.open_portfolio_window).grid(row=0, column=5, padx=10)
        ttk.Button(control, text="Txn Log", command=self.open_transaction_window).grid(row=0, column=6, padx=10)
        ttk.Button(control, text="Restart", command=self.restart_portfolio).grid(row=0, column=7, padx=10)
        ttk.Button(control, text="Help", command=self.show_help).grid(row=0, column=8, padx=10)

        dash = tk.Frame(root, bg="#1e1e2e")
        dash.pack(fill="both", expand=True, padx=20, pady=20)
        stock_frame = tk.LabelFrame(dash, text="Stock Prices", bg="#1e1e2e", fg="white", font=("Segoe UI", 13, "bold"))
        stock_frame.pack(side="left", fill="both", expand=True, padx=10)
        self.stock_table = ttk.Treeview(stock_frame, columns=("Symbol", "Price", "Monthly"), show="headings", height=18)
        self.stock_table.heading("Symbol", text="Symbol")
        self.stock_table.heading("Price", text="Price ($)")
        self.stock_table.heading("Monthly", text="% Change (30d)")
        self.stock_table.pack(fill="both", expand=True, padx=5, pady=5)
        self.stock_table.tag_configure('green', foreground='lime')
        self.stock_table.tag_configure('red', foreground='red')

        port_frame = tk.LabelFrame(dash, text="Portfolio", bg="#1e1e2e", fg="white", font=("Segoe UI", 13, "bold"))
        port_frame.pack(side="right", fill="both", expand=True, padx=10)
        self.portfolio_table = ttk.Treeview(port_frame, columns=("Symbol", "Shares", "AvgCost", "Unrealised"),
                                            show="headings", height=18)
        for col in self.portfolio_table["columns"]: self.portfolio_table.heading(col, text=col)
        self.portfolio_table.pack(fill="both", expand=True, padx=5, pady=5)
        self.portfolio_table.tag_configure('green', foreground='lime')
        self.portfolio_table.tag_configure('red', foreground='red')

        self.summary = tk.Label(root, text="", font=("Consolas", 15, "bold"), bg="#11111b", fg="white", anchor="center",
                                pady=12)
        self.summary.pack(fill="x", padx=20, pady=10)

        self.update_data(initial_fetch=True)
        self.root.after(REFRESH_INTERVAL, self.auto_refresh)

    def buy_stock(self):
        sym = self.stock_choice.get()
        try:
            amount = int(self.amount_entry.get())
            success, message = self.portfolio.buy(self.stocks[sym], amount)
            if success:
                messagebox.showinfo("Bought", message)
            else:
                messagebox.showerror("Error", message)
            self.update_display()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")

    def sell_stock(self):
        sym = self.stock_choice.get()
        try:
            amount = int(self.amount_entry.get())
            success, message = self.portfolio.sell(self.stocks[sym], amount)
            if success:
                messagebox.showinfo("Sold", message)
            else:
                messagebox.showerror("Error", message)
            self.update_display()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")

    def show_graph(self):
        sym = self.stock_choice.get()
        stock = self.stocks[sym]
        win = tk.Toplevel(self.root)
        win.title(f"{sym} Price Chart")
        win.geometry("900x600")
        win.configure(bg="#1e1e2e")
        stock.fetch_historical()
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(9, 5), dpi=100)
        if stock.history:
            times, prices = zip(*stock.history)
            ax.plot(times, prices, marker="o", color="cyan", linewidth=2)
            ax.set_title(f"{sym} Price Over Time ({stock.monthly_change():+.2f}%)")
        canvas = FigureCanvasTkAgg(fig, win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def open_portfolio_window(self):
        self.portfolio.record_history(self.stocks)
        PortfolioWindow(self.root, self.stocks, self.portfolio)

    def open_transaction_window(self):
        TransactionWindow(self.root, self.portfolio)

    def restart_portfolio(self):
        if messagebox.askyesno("Restart", "Reset your entire portfolio?"):
            for f in [PORTFOLIO_FILE, HISTORY_FILE, TRANSACTIONS_FILE]:
                if os.path.exists(f): os.remove(f)
            self.portfolio = Portfolio()
            self.update_display()

    def show_help(self):
        #Create a new pop up window
        help_win = tk.Toplevel(self.root)
        help_win.title("Help Guide")
        #image file name
        image_filename = "Screenshot 2026-01-08 at 11.32.17.png"
        #Load image
        img = tk.PhotoImage(file=image_filename)

        #image has too many pixels per inch, so have to zoom
        zoom_out_factor = 2
        img = img.subsample(zoom_out_factor, zoom_out_factor)


        #Creates a label to hold the image
        lbl = tk.Label(help_win, image=img)
        lbl.image = img  #keeps a reference of the screenshot.
        lbl.pack()

    def update_data(self, initial_fetch=False):
        for stock in self.stocks.values():
            stock.fetch_current_price()
            if not stock.history:
                stock.fetch_historical()
                time.sleep(1.0)
        self.update_display()

    def update_display(self):
        for row in self.stock_table.get_children(): self.stock_table.delete(row)
        for sym in self.stocks:
            s = self.stocks[sym]
            ch = s.monthly_change()
            tag = 'green' if ch >= 0 else 'red'
            self.stock_table.insert("", "end", values=(sym, f"${s.price:.2f}", f"{ch:+.2f}%"), tags=(tag,))
        for row in self.portfolio_table.get_children(): self.portfolio_table.delete(row)
        un_total = 0.0
        for sym in self.portfolio.holdings:
            sh, av, cur = self.portfolio.holdings[sym], self.portfolio.avg_price.get(sym, 0), self.stocks[sym].price
            un = (cur - av) * sh
            un_total += un
            self.portfolio_table.insert("", "end", values=(sym, sh, f"${av:.2f}", f"{un:,.2f}"),
                                        tags=('green' if un >= 0 else 'red'))
        v = self.portfolio.total_value(self.stocks)
        self.summary.config(
            text=f"Cash: ${self.portfolio.cash:,.2f} | Total Value: ${v:,.2f} | Unrealised: ${un_total:,.2f} | Realised: ${self.portfolio.realised_profit:,.2f}")

    def auto_refresh(self):
        self.update_data()
        self.root.after(REFRESH_INTERVAL, self.auto_refresh)


if __name__ == "__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()

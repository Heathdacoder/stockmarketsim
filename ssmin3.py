import tkinter as tk
from tkinter import ttk, messagebox
import requests
import datetime
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

API_KEY = "d3nmgf9r01qo7511n57gd3nmgf9r01qo7511n580"
TICKERS = ["AAPL","MSFT","GOOG","TSLA","AMZN","FB","NVDA","JPM","V","DIS",
           "NFLX","ADBE","PYPL","INTC","CSCO","CRM","NKE","BAC","XOM","LMT"]
REFRESH_INTERVAL = 10000  # milliseconds
PORTFOLIO_FILE = "portfolio.json"
HISTORY_FILE = "history.json"

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.price = 0
        self.history = []

    def fetch_current_price(self):
        url = f"https://finnhub.io/api/v1/quote?symbol={self.symbol}&token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            self.price = data.get("c", self.price)
        except:
            pass

    def fetch_historical(self):
        end = int(datetime.datetime.now().timestamp())
        start = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp())
        url = f"https://finnhub.io/api/v1/stock/candle?symbol={self.symbol}&resolution=D&from={start}&to={end}&token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get("s")=="ok":
                self.history = [(datetime.datetime.fromtimestamp(ts), price) for ts, price in zip(data["t"], data["c"])]
        except:
            pass

    def monthly_change(self):
        if self.history and len(self.history) > 0:
            old_price = self.history[0][1]
            if old_price != 0:
                return ((self.price - old_price)/old_price)*100
        return 0

class Portfolio:
    def __init__(self):
        self.cash = 100000
        self.holdings = {}
        self.avg_price = {}
        self.realised_profit = 0
        self.history = []
        self.load_from_json()
        self.load_history()

    def save_to_json(self):
        #Save portfolio data to JSON file.
        self.save()

    def load_from_json(self):
        #Load portfolio data from JSON file.
        self.load()

    def buy(self, stock, amount):
        cost = stock.price * amount
        if amount > 0 and cost <= self.cash:
            self.cash -= cost
            if stock.symbol in self.holdings:
                total_qty = self.holdings[stock.symbol] + amount
                total_cost = self.avg_price[stock.symbol] * self.holdings[stock.symbol] + cost
                self.avg_price[stock.symbol] = total_cost / total_qty
                self.holdings[stock.symbol] += amount
            else:
                self.holdings[stock.symbol] = amount
                self.avg_price[stock.symbol] = stock.price
            self.save_to_json()
            return True
        return False

    def sell(self, stock, amount):
        if stock.symbol in self.holdings and self.holdings[stock.symbol] >= amount and amount > 0:
            self.realised_profit += (stock.price - self.avg_price[stock.symbol]) * amount
            self.cash += stock.price * amount
            self.holdings[stock.symbol] -= amount
            if self.holdings[stock.symbol] == 0:
                del self.holdings[stock.symbol]
                del self.avg_price[stock.symbol]
            self.save_to_json()
            return True
        return False

    def total_value(self, stocks):
        total = self.cash
        for sym, qty in self.holdings.items():
            total += qty * stocks[sym].price
        return total

    def unrealised_profit(self, stocks):
        profit = 0
        for sym, qty in self.holdings.items():
            profit += (stocks[sym].price - self.avg_price[sym]) * qty
        return profit

    def record_history(self, stocks):
        self.history.append((datetime.datetime.now(), self.total_value(stocks)))
        self.save_history()

    def save(self):
        data = {
            "cash": self.cash,
            "holdings": self.holdings,
            "avg_price": self.avg_price,
            "realised_profit": self.realised_profit
        }
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(data, f)

    def load(self):
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, "r") as f:
                data = json.load(f)
                self.cash = data.get("cash", 100000)
                self.holdings = data.get("holdings", {})
                self.avg_price = data.get("avg_price", {})
                self.realised_profit = data.get("realised_profit", 0)

    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump([(dt.isoformat(), val) for dt, val in self.history], f)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                self.history = [(datetime.datetime.fromisoformat(dt), val) for dt, val in json.load(f)]

class PortfolioWindow(tk.Toplevel):
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
        unrealised = self.portfolio.unrealised_profit(self.stocks)
        realised = self.portfolio.realised_profit
        tk.Label(pnl_frame,text=f"Unrealised P&L: ${unrealised:,.2f}",bg="#1e1e2e",fg="orange",font=("Consolas",14)).pack(side="left",padx=30)
        tk.Label(pnl_frame,text=f"Realised P&L: ${realised:,.2f}",bg="#1e1e2e",fg="lime",font=("Consolas",14)).pack(side="right",padx=30)

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
        canvas = FigureCanvasTkAgg(fig,self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both",expand=True,padx=20,pady=20)
        NavigationToolbar2Tk(canvas,self).update()

class StockApp:
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
        style.configure("TButton", font=("Segoe UI",11,"bold"), padding=8, relief="flat")
        style.configure("Treeview", background="#2a2a40", foreground="white", rowheight=28, fieldbackground="#2a2a40")

        control = tk.Frame(root,bg="#1e1e2e")
        control.pack(pady=15)
        self.stock_choice = tk.StringVar()
        self.stock_menu = ttk.Combobox(control,textvariable=self.stock_choice,values=TICKERS,state="readonly",font=("Segoe UI",12))
        self.stock_menu.current(0)
        self.stock_menu.grid(row=0,column=0,padx=10)
        self.amount_entry = tk.Entry(control,font=("Segoe UI",12),justify="center",width=12)
        self.amount_entry.grid(row=0,column=1,padx=10)
        ttk.Button(control,text="Buy",command=self.buy_stock).grid(row=0,column=2,padx=10)
        ttk.Button(control,text="Sell",command=self.sell_stock).grid(row=0,column=3,padx=10)
        ttk.Button(control,text="Stock Graph",command=self.show_graph).grid(row=0,column=4,padx=10)
        ttk.Button(control,text="Portfolio",command=self.open_portfolio_window).grid(row=0,column=5,padx=10)
        ttk.Button(control,text="Restart",command=self.restart_portfolio).grid(row=0,column=6,padx=10)

        dash = tk.Frame(root,bg="#1e1e2e")
        dash.pack(fill="both",expand=True,padx=20,pady=20)

        stock_frame = tk.LabelFrame(dash,text="Stock Prices",bg="#1e1e2e",fg="white",font=("Segoe UI",13,"bold"))
        stock_frame.pack(side="left",fill="both",expand=True,padx=10)
        self.stock_table = ttk.Treeview(stock_frame,columns=("Symbol","Price","Monthly"),show="headings",height=18)
        self.stock_table.heading("Symbol",text="Symbol")
        self.stock_table.heading("Price",text="Price ($)")
        self.stock_table.heading("Monthly",text="% Change (30d)")
        self.stock_table.column("Symbol",anchor="center",width=100)
        self.stock_table.column("Price",anchor="center",width=120)
        self.stock_table.column("Monthly",anchor="center",width=120)
        self.stock_table.pack(fill="both",expand=True,padx=5,pady=5)

        port_frame = tk.LabelFrame(dash,text="Portfolio",bg="#1e1e2e",fg="white",font=("Segoe UI",13,"bold"))
        port_frame.pack(side="right",fill="both",expand=True,padx=10)
        self.portfolio_table = ttk.Treeview(port_frame,columns=("Symbol","Shares"),show="headings",height=18)
        self.portfolio_table.heading("Symbol",text="Symbol")
        self.portfolio_table.heading("Shares",text="Shares Owned")
        self.portfolio_table.column("Symbol",anchor="center",width=100)
        self.portfolio_table.column("Shares",anchor="center",width=120)
        self.portfolio_table.pack(fill="both",expand=True,padx=5,pady=5)

        self.summary = tk.Label(root,text="",font=("Consolas",15,"bold"),bg="#11111b",fg="white",anchor="center",pady=12)
        self.summary.pack(fill="x",padx=20,pady=10)

        self.update_data()
        self.root.after(REFRESH_INTERVAL,self.auto_refresh)

    def buy_stock(self):
        sym = self.stock_choice.get()
        stock = self.stocks[sym]
        try:
            amount = int(self.amount_entry.get())
        except:
            messagebox.showerror("Error","Enter a number")
            return
        if self.portfolio.buy(stock,amount):
            messagebox.showinfo("Bought",f"Bought {amount} shares of {sym}")
        else:
            messagebox.showerror("Error","Not enough cash")
        self.update_display()

    def sell_stock(self):
        sym = self.stock_choice.get()
        stock = self.stocks[sym]
        try:
            amount = int(self.amount_entry.get())
        except:
            messagebox.showerror("Error","Enter a number")
            return
        if self.portfolio.sell(stock,amount):
            messagebox.showinfo("Sold",f"Sold {amount} shares of {sym}")
        else:
            messagebox.showerror("Error","Not enough shares")
        self.update_display()

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
        ax.set_title(f"{sym} Price Over Time",fontsize=14)
        ax.set_xlabel("Date/Time")
        ax.set_ylabel("Price ($)")
        ax.grid(True,linestyle="--",alpha=0.5)
        canvas = FigureCanvasTkAgg(fig,win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both",expand=True)
        NavigationToolbar2Tk(canvas,win).update()

    def open_portfolio_window(self):
        self.portfolio.record_history(self.stocks)
        PortfolioWindow(self.root,self.stocks,self.portfolio)

    def restart_portfolio(self):
        confirm = messagebox.askyesno("Restart","Are you sure you want to reset portfolio?")
        if confirm:
            if os.path.exists(PORTFOLIO_FILE): os.remove(PORTFOLIO_FILE)
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
            self.portfolio = Portfolio()
            self.update_display()

    def update_data(self):
        for stock in self.stocks.values():
            stock.fetch_current_price()
        self.update_display()

    def update_display(self):
        for row in self.stock_table.get_children():
            self.stock_table.delete(row)
        for sym, stock in self.stocks.items():
            self.stock_table.insert("", "end", values=(sym, f"${stock.price:.2f}", f"{stock.monthly_change():+.2f}%"))
        for row in self.portfolio_table.get_children():
            self.portfolio_table.delete(row)
        for sym, shares in self.portfolio.holdings.items():
            self.portfolio_table.insert("", "end", values=(sym, shares))
        total_val = self.portfolio.total_value(self.stocks)
        self.summary.config(text=f"Cash: ${self.portfolio.cash:,.2f} | Total: ${total_val:,.2f}")

    def auto_refresh(self):
        self.update_data()
        self.root.after(REFRESH_INTERVAL,self.auto_refresh)


if __name__=="__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()

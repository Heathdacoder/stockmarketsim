import tkinter as tk
from tkinter import ttk, messagebox
import random
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class Stock:
    def __init__(self, symbol, price):
        self.symbol = symbol
        self.prices = [price]
        self.dates = [datetime.datetime.now()]

    def update_price(self):
        last = self.prices[-1]
        change = random.gauss(1.0, 0.02)  # random small change
        new_price = max(1, last * change)
        self.prices.append(new_price)
        self.dates.append(datetime.datetime.now())

    def current_price(self):
        return self.prices[-1]


class Portfolio:
    def __init__(self, cash=100000):
        self.cash = cash
        self.holdings = {}
        self.history = []  # (time, total value)

    def buy(self, stock, amount):
        cost = stock.current_price() * amount
        if amount > 0 and cost <= self.cash:
            self.cash -= cost
            self.holdings[stock.symbol] = self.holdings.get(stock.symbol, 0) + amount
            return True
        return False

    def sell(self, stock, amount):
        if amount > 0 and stock.symbol in self.holdings and self.holdings[stock.symbol] >= amount:
            self.cash += stock.current_price() * amount
            self.holdings[stock.symbol] -= amount
            if self.holdings[stock.symbol] == 0:
                del self.holdings[stock.symbol]
            return True
        return False

    def total_value(self, market):
        total = self.cash
        for sym, stock in market.stocks.items():
            total += self.holdings.get(sym, 0) * stock.current_price()
        return total

    def record_history(self, market):
        now = datetime.datetime.now()
        total_val = self.total_value(market)
        self.history.append((now, total_val))


class Market:
    def __init__(self):
        self.day = 0
        self.stocks = {
            "AAPL": Stock("AAPL", 205.30),
            "GOOG": Stock("GOOG", 175.98),
            "TSLA": Stock("TSLA", 670.05),
            "MSFT": Stock("MSFT", 1330.00),
            "NKE": Stock("NKE", 110.00),
            "BAC": Stock("BAC", 28.00),
            "LMT": Stock("LMT", 430.00),
            "DAL": Stock("DAL", 38.50),
            "XOM": Stock("XOM", 112.00),
            "RTX": Stock("RTX", 84.20),
        }

        self.events = [
            ("XOM", "Oil prices rise due to conflict", 1.15),
            ("DAL", "Travel demand falls", 0.80),
            ("LMT", "New defence contract awarded", 1.20),
            ("TSLA", "EV subsidies announced", 1.18),
            ("RTX", "Budget cuts hit aerospace", 0.85),
            ("BAC", "Banking regulations increase", 0.90),
            ("AAPL", "New iPhone release boosts sales", 1.12),
            ("GOOG", "Antitrust investigation", 0.87),
        ]

    def next_day(self):
        self.day += 1
        for stock in self.stocks.values():
            stock.update_price()

        # small chance of random event
        if random.random() < 0.15:
            sym, desc, factor = random.choice(self.events)
            stock = self.stocks[sym]
            stock.prices[-1] = max(1, stock.current_price() * factor)
            messagebox.showinfo("Market News", f"{desc}\n({sym}: x{factor:.2f})")
            return sym
        return None


class StockApp:
    def __init__(self, root):
        self.root = root
        self.market = Market()
        self.portfolio = Portfolio()

        root.title("Stock Market Simulator")
        root.geometry("1200x800")
        root.configure(bg="#1e1e2e")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e2e", foreground="white", font=("Segoe UI", 12))
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=8, relief="flat")
        style.configure("Treeview", background="#2a2a40", foreground="white", rowheight=28, fieldbackground="#2a2a40")

        control = tk.Frame(root, bg="#1e1e2e")
        control.pack(pady=15)

        self.stock_choice = tk.StringVar()
        self.stock_menu = ttk.Combobox(control, textvariable=self.stock_choice,
                                       values=list(self.market.stocks.keys()), state="readonly", font=("Segoe UI", 12))
        self.stock_menu.current(0)
        self.stock_menu.grid(row=0, column=0, padx=10)

        self.amount_entry = tk.Entry(control, font=("Segoe UI", 12), justify="center", width=12)
        self.amount_entry.grid(row=0, column=1, padx=10)

        ttk.Button(control, text="Buy", command=self.buy_stock).grid(row=0, column=2, padx=10)
        ttk.Button(control, text="Sell", command=self.sell_stock).grid(row=0, column=3, padx=10)
        ttk.Button(control, text="Next Day", command=self.next_day).grid(row=0, column=4, padx=10)
        ttk.Button(control, text="Stock Graph", command=self.show_graph).grid(row=0, column=5, padx=10)
        ttk.Button(control, text="Portfolio Graph", command=self.show_portfolio_graph).grid(row=0, column=6, padx=10)

        dash = tk.Frame(root, bg="#1e1e2e")
        dash.pack(fill="both", expand=True, padx=20, pady=20)

        stock_frame = tk.LabelFrame(dash, text="Stock Prices", bg="#1e1e2e", fg="white", font=("Segoe UI", 13, "bold"))
        stock_frame.pack(side="left", fill="both", expand=True, padx=10)

        self.stock_table = ttk.Treeview(stock_frame, columns=("Symbol", "Price"), show="headings", height=18)
        self.stock_table.heading("Symbol", text="Symbol")
        self.stock_table.heading("Price", text="Price ($)")
        self.stock_table.column("Symbol", anchor="center", width=100)
        self.stock_table.column("Price", anchor="center", width=120)
        self.stock_table.pack(fill="both", expand=True, padx=5, pady=5)

        port_frame = tk.LabelFrame(dash, text="Portfolio", bg="#1e1e2e", fg="white", font=("Segoe UI", 13, "bold"))
        port_frame.pack(side="right", fill="both", expand=True, padx=10)

        self.portfolio_table = ttk.Treeview(port_frame, columns=("Symbol", "Shares"), show="headings", height=18)
        self.portfolio_table.heading("Symbol", text="Symbol")
        self.portfolio_table.heading("Shares", text="Shares Owned")
        self.portfolio_table.column("Symbol", anchor="center", width=100)
        self.portfolio_table.column("Shares", anchor="center", width=120)
        self.portfolio_table.pack(fill="both", expand=True, padx=5, pady=5)

        self.summary = tk.Label(root, text="", font=("Consolas", 15, "bold"),
                                bg="#11111b", fg="white", anchor="center", pady=12)
        self.summary.pack(fill="x", padx=20, pady=10)

        self.update_display()

    def buy_stock(self):
        sym = self.stock_choice.get()
        stock = self.market.stocks[sym]
        try:
            amount = int(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a number")
            return

        if self.portfolio.buy(stock, amount):
            messagebox.showinfo("Bought", f"Bought {amount} shares of {sym}")
        else:
            messagebox.showerror("Error", "Not enough cash")
        self.update_display()

    def sell_stock(self):
        sym = self.stock_choice.get()
        stock = self.market.stocks[sym]
        try:
            amount = int(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a number")
            return

        if self.portfolio.sell(stock, amount):
            messagebox.showinfo("Sold", f"Sold {amount} shares of {sym}")
        else:
            messagebox.showerror("Error", "Not enough shares")
        self.update_display()

    def next_day(self):
        self.market.next_day()
        self.portfolio.record_history(self.market)
        self.update_display()

    def update_display(self):
        for row in self.stock_table.get_children():
            self.stock_table.delete(row)
        for sym, stock in self.market.stocks.items():
            self.stock_table.insert("", "end", values=(sym, f"${stock.current_price():.2f}"))

        for row in self.portfolio_table.get_children():
            self.portfolio_table.delete(row)
        for sym, shares in self.portfolio.holdings.items():
            self.portfolio_table.insert("", "end", values=(sym, shares))

        total_val = self.portfolio.total_value(self.market)
        self.summary.config(text=f"Day {self.market.day} | Cash: ${self.portfolio.cash:,.2f} | Total: ${total_val:,.2f}")

    def show_graph(self):
        sym = self.stock_choice.get()
        stock = self.market.stocks[sym]

        win = tk.Toplevel(self.root)
        win.title(f"{sym} Price Chart")
        win.geometry("900x600")
        win.configure(bg="#1e1e2e")

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(9, 5), dpi=100)
        ax.plot(stock.dates, stock.prices, marker="o", color="cyan", linewidth=2)
        ax.set_title(f"{sym} Price Over Time", fontsize=14)
        ax.set_xlabel("Date/Time")
        ax.set_ylabel("Price ($)")
        ax.grid(True, linestyle="--", alpha=0.5)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(canvas, win).update()

    def show_portfolio_graph(self):
        if not self.portfolio.history:
            messagebox.showinfo("No Data", "Advance at least one day first.")
            return

        win = tk.Toplevel(self.root)
        win.title("Portfolio Performance")
        win.geometry("900x600")
        win.configure(bg="#1e1e2e")

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(9, 5), dpi=100)

        times, values = zip(*self.portfolio.history)
        ax.plot(times, values, color="lime", marker="o", linewidth=2)
        ax.set_title("Portfolio Value Over Time", fontsize=14)
        ax.set_xlabel("Date/Time")
        ax.set_ylabel("Total Value ($)")
        ax.grid(True, linestyle="--", alpha=0.5)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(canvas, win).update()


if __name__ == "__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()

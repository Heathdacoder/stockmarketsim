import tkinter as tk
from tkinter import messagebox, ttk
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import datetime


# stock object with prices
class Stock:
    def __init__(self, symbol, price):
        self.symbol = symbol
        self.initial_price = price
        self.prices = [price]
        self.dates = [datetime.datetime.now()]

    def update_price(self):
        last_price = self.prices[-1]
        # gaussian walk (small random moves)
        change_factor = random.gauss(1, 0.02)
        new_price = max(1, last_price * change_factor)
        self.prices.append(new_price)
        self.dates.append(datetime.datetime.now())
        return new_price

    def current_price(self):
        return self.prices[-1]


# portfolio of stocks
class Portfolio:
    def __init__(self, cash=100000.0):
        self.cash = cash
        self.holdings = {}

    def buy(self, stock: Stock, amount: int):
        cost = stock.current_price() * amount
        if cost <= self.cash and amount > 0:
            self.cash -= cost
            self.holdings[stock.symbol] = self.holdings.get(stock.symbol, 0) + amount
            return True
        return False

    def sell(self, stock: Stock, amount: int):
        if self.holdings.get(stock.symbol, 0) >= amount > 0:
            self.holdings[stock.symbol] -= amount
            self.cash += stock.current_price() * amount
            return True
        return False

    def total_value(self, market):
        return self.cash + sum(
            self.holdings.get(sym, 0) * stk.current_price()
            for sym, stk in market.stocks.items()
        )


# market with stocks and random events
class Market:
    def __init__(self):
        self.day = 0
        self.SPONTANEOUS_CHANCE = 0.12  # 12% chance of event
        self.stocks = {
            "AAPL": Stock("AAPL", 205.30),
            "GOOG": Stock("GOOG", 175.98),
            "TSLA": Stock("TSLA", 670.05),
            "MSFT": Stock("MSFT", 1330.00),
            "NKE": Stock("NKE", 110.00),
            "BAC": Stock("BAC", 28.00),
            "S&P500": Stock("S&P500", 6204.95),
            "FTSE100": Stock("FTSE100", 1850.50),
            "XOM": Stock("XOM", 112.00),   # oil/energy
            "LMT": Stock("LMT", 430.00),   # defence
            "DAL": Stock("DAL", 38.50),    # airline
            "RTX": Stock("RTX", 84.20)     # aerospace/defence
        }

        # list of events (symbol, description, multiplier)
        self.events = [
            ("XOM", "Middle East tensions push oil prices higher.", 1.15),
            ("DAL", "Global pandemic fears hit airline industry.", 0.80),
            ("LMT", "Military contract signed, defence stocks surge.", 1.20),
            ("TSLA", "Government announces EV subsidies.", 1.18),
            ("RTX", "Defense budget cuts hurt aerospace firms.", 0.85),
            ("BAC", "Banking sector faces new regulations.", 0.90),
            ("AAPL", "New iPhone launch boosts Apple stock.", 1.12),
            ("GOOG", "Antitrust case filed against Google.", 0.87),
        ]

    def next_day(self):
        self.day += 1
        for stock in self.stocks.values():
            stock.update_price()

        # chance of event
        if random.random() < self.SPONTANEOUS_CHANCE:
            sym, desc, factor = random.choice(self.events)
            stock = self.stocks[sym]
            # apply shock
            shocked_price = max(1, stock.current_price() * factor)
            stock.prices[-1] = shocked_price
            messagebox.showinfo("News Event", f"Day {self.day}: {desc}\nEffect on {sym}: {factor:.2f}x")
            return sym
        return None


# tkinter app
class StockApp:
    def __init__(self, root):
        self.root = root
        self.market = Market()
        self.portfolio = Portfolio()

        # window setup
        root.title("Stock Market Simulator")
        root.geometry("1200x800")
        root.configure(bg="#1e1e2e")

        # ttk styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e2e", foreground="white", font=("Segoe UI", 12))
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=8, relief="flat")
        style.map("TButton", background=[("active", "#444")])
        style.configure("Treeview", background="#2a2a40", foreground="white", rowheight=28, fieldbackground="#2a2a40")
        style.map("Treeview", background=[("selected", "#444")])

        # control frame
        control_frame = tk.Frame(root, bg="#1e1e2e")
        control_frame.pack(pady=15)

        self.stock_choice = tk.StringVar()
        self.stock_menu = ttk.Combobox(control_frame, textvariable=self.stock_choice,
                                       values=list(self.market.stocks.keys()),
                                       state="readonly", font=("Segoe UI", 12))
        self.stock_menu.current(0)
        self.stock_menu.grid(row=0, column=0, padx=10, pady=5)

        self.amount_entry = tk.Entry(control_frame, font=("Segoe UI", 12), justify="center", width=12)
        self.amount_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Button(control_frame, text="Buy", command=self.buy_stock).grid(row=0, column=2, padx=10)
        ttk.Button(control_frame, text="Sell", command=self.sell_stock).grid(row=0, column=3, padx=10)
        ttk.Button(control_frame, text="Next Day", command=self.next_day).grid(row=0, column=4, padx=10)
        ttk.Button(control_frame, text="Show Graph", command=self.show_graph_window).grid(row=0, column=5, padx=10)

        # dashboard with stock + portfolio
        dashboard = tk.Frame(root, bg="#1e1e2e")
        dashboard.pack(fill="both", expand=True, padx=20, pady=20)

        stock_frame = tk.LabelFrame(dashboard, text="📈 Stock Prices", bg="#1e1e2e", fg="white",
                                    font=("Segoe UI", 13, "bold"))
        stock_frame.pack(side="left", fill="both", expand=True, padx=10)

        self.stock_table = ttk.Treeview(stock_frame, columns=("Symbol", "Price"), show="headings", height=18)
        self.stock_table.heading("Symbol", text="Symbol")
        self.stock_table.heading("Price", text="Price ($)")
        self.stock_table.column("Symbol", anchor="center", width=100)
        self.stock_table.column("Price", anchor="center", width=120)
        self.stock_table.pack(fill="both", expand=True, padx=5, pady=5)

        portfolio_frame = tk.LabelFrame(dashboard, text="💼 Portfolio", bg="#1e1e2e", fg="white",
                                        font=("Segoe UI", 13, "bold"))
        portfolio_frame.pack(side="right", fill="both", expand=True, padx=10)

        self.portfolio_table = ttk.Treeview(portfolio_frame, columns=("Symbol", "Shares"), show="headings", height=18)
        self.portfolio_table.heading("Symbol", text="Symbol")
        self.portfolio_table.heading("Shares", text="Shares Owned")
        self.portfolio_table.column("Symbol", anchor="center", width=100)
        self.portfolio_table.column("Shares", anchor="center", width=120)
        self.portfolio_table.pack(fill="both", expand=True, padx=5, pady=5)

        # summary bar
        self.summary = tk.Label(root, text="", font=("Consolas", 15, "bold"),
                                bg="#11111b", fg="white", anchor="center", pady=12)
        self.summary.pack(fill="x", padx=20, pady=10)

        self.update_display()

    # buy shares
    def buy_stock(self):
        stock_symbol = self.stock_choice.get()
        stock = self.market.stocks[stock_symbol]
        try:
            amount = int(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")
            return

        if self.portfolio.buy(stock, amount):
            messagebox.showinfo("Success", f"Bought {amount} shares of {stock_symbol}")
        else:
            messagebox.showerror("Error", "Not enough cash")
        self.update_display()

    # sell shares
    def sell_stock(self):
        stock_symbol = self.stock_choice.get()
        stock = self.market.stocks[stock_symbol]
        try:
            amount = int(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")
            return

        if self.portfolio.sell(stock, amount):
            messagebox.showinfo("Success", f"Sold {amount} shares of {stock_symbol}")
        else:
            messagebox.showerror("Error", "Not enough shares")
        self.update_display()

    # go to next day
    def next_day(self):
        highlight_symbol = self.market.next_day()
        self.update_display()
        if highlight_symbol:
            self.show_graph_window(highlight_symbol)

    # refresh ui
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
        self.summary.config(
            text=f" Day {self.market.day}   |   Cash: ${self.portfolio.cash:,.2f}   |   Total Value: ${total_val:,.2f} ")

    # graph of prices
    def show_graph_window(self, highlight_symbol: str = None):
        graph_win = tk.Toplevel(self.root)
        graph_win.title("Stock Price Chart")
        graph_win.geometry("900x600")
        graph_win.configure(bg="#1e1e2e")

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(9, 5), dpi=100)

        if highlight_symbol:
            stocks_to_plot = [highlight_symbol]
        else:
            stocks_to_plot = [self.stock_choice.get()]

        for sym in stocks_to_plot:
            stock = self.market.stocks[sym]
            days = list(range(len(stock.prices)))
            prices = stock.prices
            pct_change = [((p / stock.initial_price) - 1) * 100 for p in prices]

            ax.plot(days, prices, marker="o", linewidth=2, label=f"{sym} ($)")
            ax2 = ax.twinx()
            ax2.plot(days, pct_change, linestyle="--", color="orange", linewidth=1.8,
                     marker="s", markersize=5, label=f"{sym} (% Change)")

        ax.set_title(f"{stocks_to_plot[0]} Price History", fontsize=16, weight="bold", color="white")
        ax.set_xlabel("Day", fontsize=12, color="white")
        ax.set_ylabel("Price ($)", fontsize=12, color="white")
        ax2.set_ylabel("% Change", fontsize=12, color="orange")

        ax.grid(True, linestyle="--", alpha=0.5)
        ax.tick_params(colors="white")
        ax2.tick_params(colors="orange")

        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc="upper left", fontsize=10)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

# run program
if __name__ == "__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()

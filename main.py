import tkinter as tk
from tkinter import messagebox
import random

# --- Data Structures ---
stocks = {
    "AAPL": 150.0,
    "GOOG": 2800.0,
    "TSLA": 700.0,
    "BLMB": 0,
    "SMSG": 0
}

portfolio = {
    "cash": 10000.0,
    "AAPL": 0,
    "GOOG": 0,
    "TSLA": 0,
    "BLMB": 0,
    "SMSG": 0
}

day = 0

# --- Functions ---
def update_prices():
    for stock in stocks:
        change = random.uniform(-0.05, 0.05)
        stocks[stock] *= (1 + change)
    update_display()

def buy_stock():
    stock = stock_entry.get().upper()
    try:
        amount = int(amount_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number of shares.")
        return None

    if stock not in stocks:
        messagebox.showerror("Error", "Invalid stock symbol.")
        return None

    cost = stocks[stock] * amount
    if cost > portfolio["cash"]:
        messagebox.showerror("Error", "Not enough cash available.")
    else:
        portfolio["cash"] -= cost
        portfolio[stock] += amount
        messagebox.showinfo("Success", f"Bought {amount} shares of {stock}")
        update_display()

def sell_stock():
    stock = stock_entry.get().upper()
    try:
        amount = int(amount_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number of shares.")
        return None

    if stock not in stocks:
        messagebox.showerror("Error", "Invalid stock symbol.")
        return None

    if amount > portfolio[stock]:
        messagebox.showerror("Error", "Not enough shares to sell.")
    else:
        revenue = stocks[stock] * amount
        portfolio["cash"] += revenue
        portfolio[stock] -= amount
        messagebox.showinfo("Success", f"Sold {amount} shares of {stock}")
        update_display()

def next_day():
    global day
    day += 1
    update_prices()

def update_display():
    info = f"Day {day}\n\nStock Prices:\n"
    for stock, price in stocks.items():
        info += f"{stock}: ${price:.2f}\n"

    info += "\nPortfolio:\n"
    for stock in ["AAPL", "GOOG", "TSLA", "BLMB", "SMSG"]:
        info += f"{stock}: {portfolio[stock]} shares\n"

    info += f"\nCash: ${portfolio['cash']:.2f}"

    total = portfolio["cash"] + sum(portfolio[stk] * stocks[stk] for stk in stocks)
    info += f"\nTotal Value: ${total:.2f}"

    output_label.config(text=info)

# --- GUI Setup ---
root = tk.Tk()
root.title("Stock Market Simulator")

tk.Label(root, text="Stock Symbol:").grid(row=0, column=0)
stock_entry = tk.Entry(root)
stock_entry.grid(row=0, column=1)

tk.Label(root, text="Shares:").grid(row=1, column=0)
amount_entry = tk.Entry(root)
amount_entry.grid(row=1, column=1)

buy_button = tk.Button(root, text="Buy", command=buy_stock)
buy_button.grid(row=2, column=0, pady=5)

sell_button = tk.Button(root, text="Sell", command=sell_stock)
sell_button.grid(row=2, column=1)

next_day_button = tk.Button(root, text="Next Day", command=next_day)
next_day_button.grid(row=3, column=0, columnspan=2, pady=5)

output_label = tk.Label(root, text="", justify="left", font=("Courier", 10), anchor="w")
output_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10)

update_display()

root.mainloop()

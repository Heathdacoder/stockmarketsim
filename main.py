import tkinter as tk
from tkinter import messagebox
import random
import matplotlib.pyplot as plt

# Data Structures
stocks = {
    "AAPL": [205.30],
    "GOOG": [175.98],
    "TSLA": [670.05],
    "Nasdaq": [89.42],
    "SMSG": [1117.00],
    "FTSE 100": [1850.50],
    "S&P 500": [6204.95],
    "NKE": [110.00],
    "BAC": [28.00],
    "MSFT": [1330.00],
    "UK GOV BOND": [50,000]


}

portfolio = {
    "cash": 100000.0,
    "AAPL": 0,
    "GOOG": 0,
    "TSLA": 0,
    "Nasdaq": 0,
    "SMSG": 0,
    "FTSE 100": 0,
    "S&P 500": 0,
    "NKE": 0,
    "BAC": 0,
    "MSFT": 0,
    "UK GOV BOND": 0
}

day = 0

def update_prices():
    global day
    day += 1
    for stock in stocks:
        last_price = stocks[stock][-1]
        change = random.uniform(-0.05, 0.05)  # +/- 5% change
        new_price = max(0.01, last_price * (1 + change))  # Avoid prices <= 0
        stocks[stock].append(new_price)
    update_display()

def buy_stock():
    stock = stock_entry.get().upper()
    try:
        amount = int(amount_entry.get())
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid positive number of shares.")
        return

    if stock not in stocks:
        messagebox.showerror("Error", "Invalid stock symbol.")
        return

    current_price = stocks[stock][-1]
    cost = current_price * amount
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
        if amount <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid positive number of shares.")
        return

    if stock not in stocks:
        messagebox.showerror("Error", "Invalid stock symbol.")
        return

    if amount > portfolio[stock]:
        messagebox.showerror("Error", "Not enough shares to sell.")
    else:
        current_price = stocks[stock][-1]
        revenue = current_price * amount
        portfolio["cash"] += revenue
        portfolio[stock] -= amount
        messagebox.showinfo("Success", f"Sold {amount} shares of {stock}")
        update_display()

def next_day():
    update_prices()

def update_display():
    info = f"Day {day}\n\nStock Prices:\n"
    for stock, price_history in stocks.items():
        current_price = price_history[-1]
        info += f"{stock}: ${current_price:.2f}\n"

    info += "\nPortfolio:\n"
    for stock in ["AAPL", "GOOG", "TSLA", "Nasdaq","SMSG","FTSE 100","S&P 500","NKE","BAC","MSFT","UK GOV BOND"]:
        info += f"{stock}: {portfolio[stock]} shares\n"

    info += f"\nCash: ${portfolio['cash']:.2f}"

    total = portfolio["cash"] + sum(portfolio[stk] * stocks[stk][-1] for stk in stocks)
    info += f"\nTotal Value: ${total:.2f}"

    output_label.config(text=info)


def graph():
    plt.figure(figsize=(8, 5))

    max_price = 0
    max_days = 0

    for prices in stocks.values():
        if prices:
            max_price = max(max_price, max(prices))
            max_days = max(max_days, len(prices))

    for stock, prices in stocks.items():
        plt.plot(prices, label=stock)

    plt.legend()
    plt.title("Stock Prices Over Time")
    plt.xlabel("Day")
    plt.ylabel("Price ($)")

    if max_price == 0:
        plt.ylim(0, 1)
    else:
        plt.ylim(0, max_price * 1.2)

    if max_days <= 1:
        plt.xlim(-0.5, 1.5)
        plt.xticks([0], ["Day 1"])
    else:
        plt.xlim(0, max_days - 1)
        plt.xticks(range(max_days), [f"Day {i+1}" for i in range(max_days)])

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Stock Market Simulator")
    root.geometry("900x650")
    root.configure(bg="#eaeaea")

    # Fonts and colors
    label_font = ("Arial", 14)
    button_font = ("Arial", 12, "bold")
    output_font = ("Courier New", 14)
    btn_color = "#007acc"
    btn_fg = "white"

    # Frame for inputs
    input_frame = tk.Frame(root, bg="#eaeaea", pady=15)
    input_frame.pack(fill="x", padx=20)

    tk.Label(input_frame, text="Stock Symbol:", font=label_font, bg="#eaeaea").grid(row=0, column=0, sticky="e", padx=10, pady=10)
    stock_entry = tk.Entry(input_frame, font=label_font, width=15)
    stock_entry.grid(row=0, column=1, pady=10)

    tk.Label(input_frame, text="Shares:", font=label_font, bg="#eaeaea").grid(row=1, column=0, sticky="e", padx=10, pady=10)
    amount_entry = tk.Entry(input_frame, font=label_font, width=15)
    amount_entry.grid(row=1, column=1, pady=10)

    buy_button = tk.Button(input_frame, text="Buy", command=buy_stock, font=button_font, bg=btn_color, fg=btn_fg, width=12)
    buy_button.grid(row=0, column=2, rowspan=2, padx=20)

    # Frame for sell and next day
    action_frame = tk.Frame(root, bg="#eaeaea", pady=10)
    action_frame.pack(fill="x", padx=20)

    sell_button = tk.Button(action_frame, text="Sell", command=sell_stock, font=button_font, bg="#d9534f", fg=btn_fg, width=12)
    sell_button.grid(row=0, column=0, padx=15)

    next_day_button = tk.Button(action_frame, text="Next Day", command=next_day, font=button_font, bg="#6c757d", fg=btn_fg, width=26)
    next_day_button.grid(row=0, column=1, padx=15)

    # Frame for graph button
    graph_frame = tk.Frame(root, bg="#eaeaea", pady=10)
    graph_frame.pack(fill="x", padx=20)

    graph_button = tk.Button(graph_frame, text="Show Stock Graph", command=graph, font=button_font, bg="#28a745", fg=btn_fg, width=40)
    graph_button.pack(pady=10)

    # Output Label (multi-line)
    output_label = tk.Label(root, text="", justify="left", font=output_font, bg="white", fg="black", bd=2, relief="sunken", anchor="nw")
    output_label.pack(fill="both", expand=True, padx=20, pady=15)


    update_display()
    root.mainloop()
import tkinter as tk
import matplotlib.pyplot as plt
import main

root = tk.Tk()
root.geometry("400x400")
root.title("Stock Market Sim Graph")

def graph():
    plt.figure(figsize=(8, 5))

    max_price = 0
    max_days = 0

    # Find max price and max days from all stocks
    for prices in main.stocks.values():
        if prices:
            max_price = max(max_price, max(prices))
            max_days = max(max_days, len(prices))

    # Plot each stock's price history
    for stock, prices in main.stocks.items():
        plt.plot(prices, label=stock)

    plt.legend()
    plt.title("Stock Prices Over Time")
    plt.xlabel("Day")
    plt.ylabel("Price ($)")

#y, axis ticks
    if max_price == 0:
        plt.ylim(0, 1)
    else:
        plt.ylim(0, max_price * 1.2)

#x, axis ticks
    if max_days <= 1:
        plt.xlim(-0.5, 1.5)
        plt.xticks([0], ["Day 1"])
    else:
        plt.xlim(0, max_days - 1)
        plt.xticks(range(max_days), [f"Day {i+1}" for i in range(max_days)])

    plt.tight_layout()
    plt.show()

graph_button = tk.Button(root, text="Show Stock Graph", command=graph)
graph_button.pack(pady=20)

root.mainloop()


import tkinter as tk
import matplotlib.pyplot as plt
import main

root = tk.Tk()
root.geometry("400x400")
root.title("Stock Market Sim graph")

def graph():
    plt.figure(figsize=(8,5))
    for stock, prices in main.stocks.items():
        plt.plot(prices, label=stock)
    plt.legend()
    plt.title("Stock Prices Over Time")
    plt.xlabel("Day")
    plt.ylabel("Price ($)")
    plt.show()



graph()


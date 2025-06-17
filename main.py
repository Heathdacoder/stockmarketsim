import random

stocks = {
    "AAPL": 150.0,
    "GOOG": 2800.0,
    "TSLA": 700.0
}

portfolio = {
    "cash": 10000.0,
    "AAPL": 0,
    "GOOG": 0,
    "TSLA": 0
}

def show_prices():
    print("Stock Prices:")
    for stock, price in stocks.items():
        print(f"{stock}: ${price:.2f}")

def show_portfolio():
    print("Portfolio:")
    for stock in ["AAPL", "GOOG", "TSLA"]:
        print(f"{stock}: {portfolio[stock]} shares")
    print(f"Cash: ${portfolio['cash']:.2f}")

def update_prices():
    for stock in stocks:
        change = random.uniform(-0.05, 0.05) #gives you a random floating point number in the range [a, b]
        stocks[stock] *= (1 + change)

def buy_stock():
    stock = input("Enter stock symbol: ").upper()
    if stock not in stocks:
        print("Invalid stock.")
        return
    try:
        amount = int(input("Enter number of shares to buy: "))
    except:
        print("Invalid amount.")
        return
    cost = stocks[stock] * amount
    if cost > portfolio["cash"]:
        print("Not enough cash.")
    else:
        portfolio["cash"] -= cost
        portfolio[stock] += amount
        print(f"Bought {amount} shares of {stock}")

def sell_stock():
    stock = input("Enter stock symbol: ").upper()
    if stock not in stocks:
        print("Invalid stock.")
        return
    try:
        amount = int(input("Enter number of shares to sell: "))
    except:
        print("Invalid amount.")
        return
    if amount > portfolio[stock]:
        print("Not enough shares.")
    else:
        revenue = stocks[stock] * amount
        portfolio["cash"] += revenue
        portfolio[stock] -= amount
        print(f"Sold {amount} shares of {stock}")

def show_total_value():
    total = portfolio["cash"]
    for stock in stocks:
        total += portfolio[stock] * stocks[stock]
    print(f"Total Portfolio Value: ${total:.2f}")

def main():
    days = 0
    while True:
        print(f"\nDay {days}")
        show_prices()
        show_portfolio()
        show_total_value()
        print("1. Buy")
        print("2. Sell")
        print("3. Next Day")
        print("4. Quit")
        choice = input("Choose an action: ")
        if choice == "1":
            buy_stock()
        elif choice == "2":
            sell_stock()
        elif choice == "3":
            update_prices()
            days += 1
        elif choice == "4":
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()

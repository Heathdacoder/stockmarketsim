import requests
import datetime
import json
import os
import random
import requests.exceptions
from api_handler import API_KEY

PORTFOLIO_FILE = "portfolio.json"
HISTORY_FILE = "history.json"
TRANSACTIONS_FILE = "transactions.json"

# DATA CLASSES
class Stock:
    """
    Represents a single stock in the market.
    It holds the stock's ticker symbol, its current live price, and a history
    of its past prices which will be used for rendering the Matplotlib graphs.
    """
    def __init__(self, symbol):
        self.symbol = symbol
        self.price = 0
        self.history = []

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

    def fetch_historical(self):
        end = int(datetime.datetime.now().timestamp())
        start = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp())

        url = f"https://finnhub.io/api/v1/stock/candle?symbol={self.symbol}&resolution=D&from={start}&to={end}&token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
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
                self.generate_mock_history()

        except requests.exceptions.RequestException:
            self.generate_mock_history()

    def generate_mock_history(self):
        self.history = []
        if self.price == 0:
            return

        base_price = self.price
        for i in range(30):
            day = datetime.datetime.now() - datetime.timedelta(days=(30 - i))
            movement = random.uniform(-0.02, 0.02)
            base_price = base_price * (1 + movement)
            self.history.append((day, base_price))

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
    """
    Handles all the business logic for the user's account.
    """
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

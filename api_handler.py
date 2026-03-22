# Function to get the API key safely
def load_api_key():
    """
    Returns my Finnhub API key.
    I separated this into a function so it's easier to manage or hide later
    if I decide to upload this project to GitHub.
    """
    return "enter api key here please."

API_KEY = load_api_key()

# A list of all the stock symbols we are going to use
TICKERS = ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN", "FB", "NVDA", "JPM", "V", "DIS",
           "NFLX", "ADBE", "PYPL", "INTC", "CSCO", "CRM", "NKE", "BAC", "XOM", "LMT"]

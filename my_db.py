import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

tickers = ["AAPL", "GOOG", "TSLA", "MSFT", "NKE", "BAC", "LMT", "DAL", "XOM", "RTX"]
end_date = datetime.today()
print(end_date)

#set start_date to 2 years ago
start_date = end_date - timedelta(days = 2*365)
print(start_date)

#download close prices
close_df = pd.DataFrame()

for ticker in tickers:
    data = yf.download(ticker, start=start_date, end=end_date)
    close_df[ticker] = data["Close"]

print(close_df)

output_folder = r"C:\Users\Ryan\Documents\YouTube Videos\Python Tutorials\Retrieve Stock Prices and Export to Excel"

## Export the DataFrame to Excel
output_file = os.path.join(output_folder, 'stock_prices.xlsx')
close_df.to_excel(output_file)
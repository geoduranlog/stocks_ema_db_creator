#================================================================
#=========RavenPack Test - Financial DB and EMA Computations=====
#================================================================
# Alejandro Duran - 
#09.07.2024
#--python3.10.14

##
"""
SUMMARY: Bring stock market data from 2020, store it in a SQLite database, calculate the Exponential Moving Average (EMA) for each ticker (20 in total).

PROCEDURE:
1. Load the data from the Yahoo Finance API.
2. Store the data in a single table of a SQLite database -> "stock_prices_table".
3. Calculate the Exponential Moving Average (EMA) for each ticker. 
4. Plot it for one ticker as an example.


RUN it as:

python .\RavenPack_test.py    => with default values (lookback=10 days, halflife=3.454)

python .\RavenPack_test.py --lbk 12 --hlf 3.4  => with values defined by the user [lnk:lookback, hlf:halflife].  halflife has priority 

"""

# ## ========= Clear all Variables ========
# def clear_user_vars():
#     for var_name in list(globals().keys()):
#         if not var_name.startswith("__") and var_name not in ["clear_user_vars"]:
#             globals().pop(var_name, None)
# clear_user_vars()   #QC     globals()



##=========== Import dependencies =========
import os
import yfinance as yf
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import argparse
import hashlib

#================================================================
#========================== Functions ===========================
#================================================================

# Function to generate a unique numerical ID for each stock
def generate_stock_id(ticker):
    unique_string = f"{ticker}"
    # Generate SHA-256 hash and convert to an integer
    hash_object = hashlib.sha256(unique_string.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    # Reduce the range of the hash
    max_id_value = 10**8  # 10**12 for a 12-digit ID. -> total number of unique publicly traded companies globally is ~ 60000.
    hash_int = hash_int % max_id_value
    return hash_int



#================================================================
#========================== BODY CODE ===========================
#================================================================

# --- Load the data from the yahoo finance --
# Choose 20 tickers and a start date from 2020 onwards
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'BRK-A', 'JPM', 'JNJ', 'V', 'UNH', 'PG', 'NVDA', 'HD', 'MA', 'PYPL', 'DIS', 
'INTC', 'CMCSA', 'XOM']
ticker_ids = [generate_stock_id(ticker) for ticker in tickers]
ticker_to_id = dict(zip(tickers, ticker_ids)) # Mapping
start_date = "2020-01-01"

# Bring data
data = yf.download(tickers, start=start_date)



# #---  QC input data
# data.shape
# data.info()
# data.describe()

# # ... check NaN values
# data.isnull().sum()

# # tickers with NaN values
# nan_tickers = data.isnull().sum().sort_values(ascending=False)
# nan_tickers = nan_tickers[nan_tickers > 0]
# len(nan_tickers)




# --- Save the data to a sqlite DB ---
database_name = 'stock_prices.db'# Name of the database (saved in current directory)

# Check if the database already exists, if not, create it (although it is the same command)
if not os.path.exists(database_name):
    print(f"Creating database: {database_name}")

    # Create the DB
    conn = sqlite3.connect(database_name)
    print("Database created successfully.")

else:
    print(f"Database {database_name} already exists.")
    # Connect to the existing DB
    conn = sqlite3.connect(database_name)


# Create cursor object (to execute SQL queries)
c = conn.cursor()




# # --- Create a table in the database to store the stock prices ---
# Drop table (for testing purposes) 
c.execute('''DROP TABLE IF EXISTS stock_prices_table''')


# Create table with a composite primary key
c.execute('''CREATE TABLE IF NOT EXISTS stock_prices_table
             (date_ticker_id REAL PRIMARY KEY, Date DATE, Open REAL, Close REAL, Ticker TEXT)
            ''')


# Store data in one table
for ticker in tickers:
    ID_df = pd.DataFrame((data['Open'][ticker].reset_index()['Date'].dt.strftime('%Y%m%d') + data['Open'][ticker].reset_index().index.map(lambda x: ticker_to_id[ticker]).astype(str)).astype(int), columns=['date_ticker_id'])
    df = data['Open'][ticker].reset_index().rename(columns={ticker: 'Open'})
    df['Close'] = data['Close'][ticker].values
    df['Ticker'] = ticker
    df = pd.concat([ID_df, df], axis=1) # concatenate to include primary key
    df.to_sql('stock_prices_table', conn, if_exists='append', index=False)

conn.commit()




# --- Get parameters from the user ---
# Create the parser
parser = argparse.ArgumentParser(description='Process input parameters (lookbak and/or half-life) for EMA computation ')

# Add arguments
parser.add_argument('--lbk', type=int, help='The lookback (i.e., span or period considered) value')
parser.add_argument('--hlf', type=float, help='The half-life value')
args = parser.parse_args()

# Set defaults if none argument are provided
span = args.lbk if args.lbk is not None else 10  # Default lookback value is 10 days (if not provided by user)
halflife = args.hlf


# If halflife is not provided, calculate it using lookback
if halflife is None:
    alpha = 2 / (span + 1)  # standard alpha equation (smoothing factor) using lookback period
    halflife = -np.log(2) / np.log(1 - alpha)
else:
    alpha = 1 - np.exp(np.log(0.5) / halflife)

print(f"Lookback: {span}, halflife: {halflife}")





# ====== Computation of EMA - Exponential Moving Average ======
# Here I will bring the data from the SQL table and calculate the EMA for each ticker

# Load all data (from main table) into a DataFrame
df_stocks = pd.read_sql_query("SELECT Date, Close, Ticker FROM stock_prices_table ORDER BY Ticker, Date", conn)

# -- EMA for each ticker
df_stocks['EMA_Close'] = df_stocks.groupby('Ticker')['Close'].transform(lambda x: x.ewm(halflife=halflife, adjust=False).mean())
#df_stocks['EMA_Close'] = df_stocks.groupby('Ticker')['Close'].transform(lambda x: x.ewm(halflife=halflife,  min_periods=span, adjust=False).mean())


# --- Figure: Price evolution and EMA for a specific ticker
ticker_plot = 'AAPL' # Choose the ticker to plot
plt.figure(figsize=(12, 6))
plt.plot(df_stocks[df_stocks.Ticker==ticker_plot].Date, df_stocks[df_stocks.Ticker==ticker_plot].Close, label='Close Price')
plt.plot(df_stocks[df_stocks.Ticker==ticker_plot].Date, df_stocks[df_stocks.Ticker==ticker_plot].EMA_Close, label='EMA Close', linestyle='--')
plt.legend()
plt.title(f'{ticker_plot} Stock Prices and {span}-day EMA ')
plt.grid()
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(nbins=10))  # Limit the number of x-axis ticks
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
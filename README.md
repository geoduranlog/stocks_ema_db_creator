# stocks_ema_db_creator
Bring stock market data from 2020, store it in a SQLite database, and calculate the Exponential Moving Average (EMA) for each ticker (20 in total).


## PROCEDURE:
1. Load the data from the Yahoo Finance API.
2. Store the data in a single table of a SQLite database -> "stock_prices_table".
3. Calculate the Exponential Moving Average (EMA) for each ticker. 
4. Plot it for one ticker as an example.


## RUN it as:
```
python .\RavenPack_test.py    ## => with default values (lookback=10 days, halflife=3.454)

python .\RavenPack_test.py --lbk 12 --hlf 3.4    ## => with values defined by the user [lbk:lookback, hlf:halflife].  halflife has priority 

```

## NOTES
- The code will authomatically make the plot of close prices and EMA of close prices for the ticker 'AAPL' (Apple).
- EMA is computing using a smoothing factor (alpha). Alpha can be computed in different ways
  -  using the half life -> alpha = 1-exp(ln(0.5)/halflife),
  -  or using the lookback -> alpha=2/(lookback+1).
  
  *I  gave priority to the using of halflife, but if it is not provided by the user, I used a default lookback =10 days to compute alpha*

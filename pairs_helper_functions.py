
import ccxt
from pprint import pprint
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date, timedelta
import matplotlib
import numpy as np

def get_historical_data(start_date, market, resolution):
  """
  Downloads OHLCV data from ftx
  TODO : aggregate ohlcv data from all exchanges 
  TODO : consolidate perpetual vs spot markets
  start_date - string of start date ex. "2022-04-01"
  market - name of market to download
  resolution - resolution of candlestick
  returns: OHLCV data
  """
  exchange = ccxt.ftx({'enableRateLimit': True})
  start_date = exchange.parse8601(f"{start_date}T00:00:00Z")
  params = {'market_name': market}  # https://github.com/ccxt/ccxt/wiki/Manual#overriding-unified-api-params
  limit = None
  # specify any existing symbol here ↓ (it does not matter, because it is overrided in params)
  ohlcv = exchange.fetch_ohlcv(market, resolution, start_date, limit, params)
  return ohlcv

def ls_index(start_date, long, short, resolution):
  """
  Returns dataframe of returns data of index
  start_date - string of start date ex. "2022-04-01"
  long - name of market to long
  short - name of market to short
  resolution - resolution of candlestick ex. "1h"
  returns: DataFrame of returns
  """
  try:
    s = read_historical_data(start_date, short, resolution)
    l = read_historical_data(start_date, long, resolution)
  except FileNotFoundError as e:
      s_name = download_historical_data(start_date, short, resolution)
      l_name = download_historical_data(start_date, long, resolution)
      s = read_historical_data(start_date, short, resolution)
      l = read_historical_data(start_date, long, resolution)
  df = pd.DataFrame(columns=['time','l','s'])
  df['time'] = s['time']
  df['s'] = s['close']
  df['l'] = l['close']
  df['ls'] = df['l'] / df['s']
  df['returns'] = df['ls'] / df['ls'][0]
  
  return df

def download_historical_data(start_date, ticker, resolution):
    """
    Downloads historical data into specific folder
    start_date - string of start date ex. "2022-04-01"
    ticker - ticker to download
    resolution - resolution of candlestick ex. "1h"
    returns: String of filename
    """
    import os
    data = get_historical_data(start_date, ticker, resolution)
    file_name = f"{ticker}_{resolution}_{start_date}.csv"
    outdir = 'data'
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    fullname = os.path.join(outdir, file_name)  


    df = pd.DataFrame(data, columns=['time','open','high','low','close','volume'])
    df.to_csv(fullname)
    return file_name

def read_historical_data(start_date, ticker, resolution):
    """
    Reads historical data from subfolder
    start_date - string of start date ex. "2022-04-01"
    ticker - ticker to download
    resolution - resolution of candlestick ex. "1h"
    returns: OHLCV DataFrame
    """
    data = pd.read_csv(f"data/{ticker}_{resolution}_{start_date}.csv")
    return pd.DataFrame(data, columns=['time','open','high','low','close','volume'])

def compare(date, ticker, res="1h",long=False,tickers = ["BTC","ETH","LUNA", "SOL","AVAX","BNB","MATIC","NEAR","ATOM","ADA"]):
  """
  Compares one ticker to a variety of different tickers
  date - string of start date ex. "2022-04-01"
  ticker - ticker to use as base
  res - resolution of candlestick ex. "1h"
  long - Long or short the ticker
  tickers - list of tickers to compare against
  """
  sz = int(len(tickers) / 2)
  fig, axs = plt.subplots(2,sz,figsize=(20,15))
  
  info_list = list()
  if long:
    for i in range(len(tickers)):
      df = ls_index(date, ticker, tickers[i]+"-PERP", res)
      long = ticker.removesuffix("-PERP")
      axs[int(i/sz)][int(i%sz)].set_title(f"{long}/{tickers[i]}")
      axs[int(i/sz)][int(i%sz)].plot(df['time'], df['returns'])     
      max, min, cur = analyze(df)
      info_list.append([f"{long}/{tickers[i]}",max,min,cur])
      
    plt.show()
  
        
  else:
      for i in range(len(tickers)):
        df = ls_index(date, tickers[i]+"-PERP",ticker, res)
        long = ticker.removesuffix("-PERP")
        axs[int(i/sz)][int(i%sz)].set_title(f"{tickers[i]}/{long}")
        axs[int(i/sz)][int(i%sz)].plot(df['time'], df['returns'])     
        max, min, cur = analyze(df)
        info_list.append([f"{tickers[i]}/{long}",max,min,cur])
    
  info = pd.DataFrame(info_list,columns=['pair','max_drawdown','max_return','current_return'])
  return info
    
def analyze(df):
    """
    Calculates some stats about the returns
    df - DataFrame of returns to analyze
    Returns: 3-tuple
    """
    def max_drawdown(returns):
      high = 0
      max_dd = 0
      for i,val in enumerate(returns):
          if val > high:
              high = val
              dd = high - min(returns[i:])
              if dd > max_dd:
                  max_dd = dd
      return max_dd
    
    size = len(df) 
    # print(f"In {size} hours ({round(size/24)} days), {t1.removesuffix('-PERP')}/{t2} returned {round((df.iloc[size-1]['returns'] - 1) * 100,2)}%")
    maxdrawdown =  round((min(df['returns']) - 1 )*100,2)
    max_return =  round((max(df['returns'])-1) * 100,2)
    # print(f"The max drawdown was {maxdrawdown}% and the max return was {max_return}%")
    current_return = (df['returns'][size-1] - 1) * 100
    return maxdrawdown, max_return, current_return

def index_chart(long, short, start_date):
  """
  Plots the long/short index via matplotlib
  long - ticker to long
  short - ticker to short
  start_date - string of start date ex. "2022-04-01"
  """
  fxs_waves = ls_index(start_date, long, short, "1h")
  plt.plot(fxs_waves['time'],fxs_waves['returns'])
  a,b,c = analyze(fxs_waves, long, short)
  print(f"{long}/{short} since {start_date}")
  print(f"max drawdown: {round(max_drawdown(fxs_waves['returns'])*100,2)}%") 
  print(f"max return: {b}%")
  print(f"current return: {round(c,2)}%")
  print(f"% to max: {round(b-c,2)}%")

def remove_data():
    import os
    import glob
    for f in glob.glob("data/*"):
        os.remove(f)

def multi_weighted_index(weights, lookback_window = 30, resolution="1h"):
    """
    Multiweighted index visualizer
    weights - dictionary of tickers with respective weights (negative weight indicates short)
    lookback_window - lookback period in days
    starting_balance - starting balance
    """
    start_date = date.today() - timedelta(lookback_window)
    ohlc_data = dict()
    holding = dict()
    returns = pd.DataFrame()
    for ticker in weights.keys():
        try:
            ohlc = read_historical_data(start_date, f"{ticker}-PERP", resolution)
        except FileNotFoundError as e:
            ohlc_filename = download_historical_data(start_date, f"{ticker}-PERP", resolution)
            ohlc = read_historical_data(start_date, f"{ticker}-PERP", resolution)
        
        ohlc[f"return_{ticker}"] = (ohlc['close'] - ohlc['open'][0]) / ohlc['open'][0]
        returns[ticker] = ohlc[f"return_{ticker}"]

    for k,v in weights.items():
        returns[k] = returns[k] * v
    returns["cum_returns"] = returns.sum(axis=1)
    remove_data()

    plt.figure(figsize=(15,10))
    plt.plot(returns["cum_returns"], color='black', label='return')
    for ticker in weights.keys():
        plt.plot(returns[ticker], label=ticker)
    plt.legend()


    return returns

def multi_weighted_index_v2(weights, lookback_window , resolution="1h"):
    """
    Multiweighted index visualizer
    weights - dictionary of tickers with respective weights (negative weight indicates short)
    lookback_window - lookback period in days
    starting_balance - starting balance
    """
    start_date = date.today() - timedelta(int(lookback_window))
    returns = pd.DataFrame()
    for ticker in weights.keys():
        download_historical_data(start_date, f"{ticker}-PERP", resolution)
        ohlc = read_historical_data(start_date, f"{ticker}-PERP", resolution)
        ohlc[f"return_{ticker}"] = (ohlc['close'] - ohlc['open'][0]) / ohlc['open'][0]
        returns[ticker] = ohlc[f"return_{ticker}"]

    for k,v in weights.items():
        returns[k] = returns[k] * v

    returns["returns"] = returns.sum(axis=1)
    ohlc['time'] = ohlc['time'] / 1000
    returns = returns.set_index(ohlc['time'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M')))
    returns.plot(figsize=(20, 10))

    remove_data()

    return returns
    
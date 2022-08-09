

#####################################################################

# Unfinished functions
import numpy as np
import time
import threading
from datetime import datetime, timedelta
# WORK IN PROGRESS FUNCTIONS
def deviation_checker():
    """
    TODO : incomplete
    """
    data = get_historical_data("01-01-2022", "ETH/USD", "1d")
    df = pd.DataFrame(data, columns=["time","open","high","low","close","volume"])
    df["daily_return"] = 100*(df['close']/df['open'] - 1)
    mean = df['daily_return'].mean()
    std = np.std(df['daily_return'])
    a = [mean+i*std for i in range(-3,4)]

    plt.figure(figsize=(15,10))
    plt.hist(df['daily_return'],50)
    def sim(df, deviations):
        pos, cost = [0,0]
        dr = df['daily_return']
        close = df['close']
        for index, pct in enumerate(dr):
            if pct < deviations[0]:
                pos += 1
                cost += close[index]
            elif pct > deviations[5]:
                pos -= 1
                cost -= close[index]
            print(pos, cost, pct)

def fetch_prices(ftx, weights, name):
    # markets = ftx.load_markets()
    last_price = dict()
    for ticker, weight in weights.items():
        # price = markets[f"{ticker}/USD:USD"]['info']['last']
        price = ftx.fetch_ticker(f"{ticker}-PERP")['ask']
        last_price[ticker] = (price)
        with open(f"{name}/{ticker}.csv", 'a') as f:
            f.write("%s\n"%(price,))
            f.close()

def roll(df, w):
    # stack df.values w-times shifted once at each stack
    roll_array = np.dstack([df.values[i:i+w, :] for i in range(len(df.index) - w + 1)]).T
    # roll_array is now a 3-D array and can be read into
    # a pandas panel object
    panel = pd.Panel(roll_array, 
                     items=df.index[w-1:],
                     major_axis=df.columns,
                     minor_axis=pd.Index(range(w), name='roll'))
    # convert to dataframe and pivot + groupby
    # is now ready for any action normally performed
    # on a groupby object
    return panel.to_frame().unstack().T.groupby(level=0)

def beta(df):
    # first column is the market
    X = df.values[:, [0]]
    # prepend a column of ones for the intercept
    X = np.concatenate([np.ones_like(X), X], axis=1)
    # matrix algebra
    b = np.linalg.pinv(X.T.dot(X)).dot(X.T).dot(df.values[:, 1:])
    return pd.Series(b[1], df.columns[1:], name='Beta')

def create_index(ftx,  weights, amount):
    import csv,os
    name = input("Index Name?: ")
    os.mkdir(name)
    with open(f"{name}/weights.csv", 'a') as f:
        for key in weights.keys():
            f.write("%s,%s,%s\n"%(key,weights[key], weights[key]*amount))
        f.close()
    
    
    track = True
    while track:
        fetch_prices(ftx, name)
        time.sleep(60)
        t = input("Stop")
        if t == "x":
            track = False

def get_24hr_data(market, resolution):
    now = datetime.now() - timedelta(days=2)    
    exchange = ccxt.ftx({'enableRateLimit': True})
    since_text = now.strftime("%m-%d-%YT00:00:00Z")
    print(since_text)
    since = exchange.parse8601(since_text)
    print(since)
    params = {'market_name': market}  # https://github.com/ccxt/ccxt/wiki/Manual#overriding-unified-api-params
    limit = None
    # specify any existing symbol here ↓ (it does not matter, because it is overrided in params)
    ohlcv = exchange.fetch_ohlcv(market, resolution, since, limit, params)
    print(ohlcv)
    return ohlcv

def spot_to_perp_ratio(ticker):
    perp = get_24hr_data(f"{ticker}-PERP", "4h")
    spot = get_24hr_data(f"{ticker}/USD", "4h")
    ratio = list()
    
    # s,p = [i[5] for i in spot], [i[5] for i in perp] 
    print(len(spot))
    print(spot)
    # s_df, p_df = pd.DataFrame(s), pd.DataFrame(p)

    # ratio = s_df.diff()[1:] / p_df.diff()[1:]
    # rv_spot_volume, rv_perp_volume = spot[0][5], perp[0][5]
    # for i in range(1,len(perp)):
    #     rv_spot_volume += spot[i][5]
    #     rv_perp_volume += perp[i][5]
    #     t0 = (spot[i-1][5] - spot[i][5]) / spot[i-1][5]
    #     t1 = (perp[i-1][5] - perp[i][5]) / perp[i-1][5]
    #     ratio.append(rv_spot_volume/rv_perp_volume)
    #     s.append(spot[i][5] / spot[0][5])
    #     p.append(perp[i][5] / perp[0][5])
        # ratio.append(spot[i][5] / perp[i][5])
    # for i, vol in enumerate(s):
    #     ratio.append(vol / p[i])

    # rel_df = pd.DataFrame(ratio, columns=["relative s/p ratio"])
    # rel_df.plot()

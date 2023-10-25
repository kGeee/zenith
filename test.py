from oms import OMS
import utils, json, time
import eth_account
from eth_account.signers.local import LocalAccount
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
import asyncio

config = utils.get_config()
account: LocalAccount = eth_account.Account.from_key(config["secret_key"])
info = Info(constants.TESTNET_API_URL, skip_ws=True)
# Change this address to a vault that you lead
vault = None

o = OMS(config, account, vault)
# for i in range(5):
#     orders = o.range(False, 4, "BLZ", (2.19,2.195), 50, 10)
#     o.bulk(orders)

# o.create_grid("SOL", 2, (36, 38), (31, 29), 20, 10)
# o.oms.order("ETH", False, .01, 1670, {"limit": {"tif": "Gtc"}})


# index
"""
1. get tickers and weight (negative weight indicates short)
2. send orders placed at current mid price from info.all_mids
"""
def hl_index(weights, total_notional):
    # weights = {'SOL':.5, 'ETH':-.5, 'BTC':.3}
    # total_notional = 4000

    if len(weights) == 0:
        sz = input(f"# of tickers: ")
        total_notional = float(input(f"Total Notional to enter ($): "))
        duration = int(input("Duration to enter (Minutes): "))
        orders = int(input("Total number of orders: "))
        for i in range(int(sz)):
            symbol = input("Ticker: ")
            weight = float(input("Weight: "))
            weights[symbol.upper()] = weight


    markets = info.all_mids()
    orders = []
    for symbol, weight in weights.items():
        value = round((weight * total_notional)  / float(markets[symbol]),2)
        side = True if weight > 0 else False
        print("buying", side, symbol, "size", value)
        orders.append(
            {
                    "coin": symbol,
                    "is_buy": side,
                    "sz": abs(value),
                    "limit_px": round(float(markets[symbol]),2),
                    "order_type": {"limit": {"tif": "Gtc"}},
                    "reduce_only": False,
                }
        )
    print(o.oms.bulk_orders(orders))

def beta_calc(symbol):
    # use btc as beta
    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    def get_candles(symbol, interval, lookback=7):
        start = int((datetime.now(timezone.utc) - timedelta(days=lookback)).timestamp() * 1e3)
        end = int(datetime.now(timezone.utc).timestamp() * 1e3)
        closes = [float(i['c']) for i in info.candles_snapshot(symbol, interval, start, end)]
        return pd.DataFrame(closes, columns=['close'])

    a = get_candles(symbol, '1h')
    b = get_candles('BTC', '1h')

    asset_returns = a['close'].pct_change().dropna()
    market_returns = b['close'].pct_change().dropna()

    # Calculate the covariance between asset and market returns
    cov = np.cov(asset_returns, market_returns)[0, 1]
    
    # Calculate the variance of market returns
    market_var = np.var(market_returns)
    
    # Calculate the beta as the covariance divided by the market variance
    beta = cov / market_var

    return beta

def get_positions():
    positions = [i for i in info.user_state(account.address)['assetPositions'] if i['position']['entryPx'] != None]
    pos = {i['position']['coin']:{'positionValue':float(i['position']['positionValue']), 'size': float(i['position']['szi']), 'uPnl': float(i['position']['unrealizedPnl'])} for i in positions}
    
    for i in pos.keys():
        beta = beta_calc(i)
        pos[i]['beta'] = round(beta,3)
        pos[i]['betaWeighted'] = pos[i]['positionValue'] * beta * -1 if pos[i]['size'] < 0 else pos[i]['positionValue'] * beta

    print(pos)
    total_position_value = round(sum([i['positionValue'] for i in pos.values()]),2)
    total_pnl = round(sum([i['uPnl'] for i in pos.values()]),2)
    total_beta_weight = round(sum([i['betaWeighted'] for i in pos.values()]),2)
    print(total_position_value, total_beta_weight, total_pnl)


get_positions()
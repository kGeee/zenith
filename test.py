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
import cProfile
import asyncio



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
    user = account.address if vault is None else vault
    positions = [i for i in info.user_state(user)['assetPositions'] if i['position']['entryPx'] != None]
    pos = {i['position']['coin']:{'positionValue':float(i['position']['positionValue']), 'size': float(i['position']['szi']), 'uPnl': float(i['position']['unrealizedPnl'])} for i in positions}
    
    for i in pos.keys():
        beta = beta_calc(i)
        pos[i]['beta'] = round(beta,3)
        pos[i]['betaWeighted'] = pos[i]['positionValue'] * beta * -1 if pos[i]['size'] < 0 else pos[i]['positionValue'] * beta

    # print(pos)
    total_position_value = round(sum([i['positionValue'] for i in pos.values()]),2)
    total_pnl = round(sum([i['uPnl'] for i in pos.values()]),2)
    total_beta_weight = round(sum([i['betaWeighted'] for i in pos.values()]),2)
    print("total value", total_position_value, total_beta_weight) 
    print("total pnl",  total_pnl)
    return {
        'positions': pos,
        'totalPositionValue': total_position_value,
        'totalBetaWeight': total_beta_weight
    }

def get_open_orders():
    user = account.address if vault is None else vault
    return info.open_orders(user)

async def cancel_open_orders(coin, resting):
    open_orders = [{'coin': coin, 'oid': i['oid']} for i in resting if i['coin'] == coin]
    o.oms.bulk_cancel(open_orders)
    print("cancelled open", coin, "orders")

async def grid(coin, markets, spread):
    mid = float(markets[coin])
    sell1, sell2 = mid * (1+spread['sell'][0]), mid * (1+spread['sell'][1])
    buy1, buy2  = mid * (1-spread['buy'][0]), mid * (1-spread['buy'][1])
    o.create_grid(coin, 2, (sell1, sell2), (buy1, buy2), spread['inventory']/mid, 10)

async def mm(spreads):
    """
    coins: list of coins to make spreads on
    spread: dict of spread config
    refresh_rate: how often to refresh grid orders (minutes)
    inventory: dict of inventory to use

    In order to mm, we need to create a grid of orders around the mid price. This grid will refresh every refresh_rate minutes.
    We need to create some kind of dynamic activity on the grid where if we fully fill the grid, we can stop making new orders for the side that is filled and
    only update the take profit side.

    Use o.create_grid("SOL", 2, (36, 38), (31, 29), 20, 10) to create orders on the coins scaled via the spread
    i.e. spread = {'SOL': (buy_spread, sell_spread)} (0.01, 0.03)

    """
    markets = info.all_mids()
    resting = info.open_orders(account.address)

    await asyncio.gather(*(cancel_open_orders(coin,resting) for coin in spreads.keys()))    
    await asyncio.gather(*(grid(coin, markets, spreads[coin]) for coin in spreads.keys() )  )

def rebalance(weights = {'SOL':.3, 'AVAX':.2, 'ATOM':.5, 'ETH':-.25}, value = 1000):
    """
    take in weights and rebalance portfolio
    1. get current positions
    2. get desired positions based on $ allocated
    3. generate orders for desired positions
    """
    positions = get_positions()
    markets = info.all_mids()
    usd_vals = {k:v*value for k,v in weights.items()}
    current_pos = {k:(v['positionValue'], v['positionValue'] / v['size']) for k,v in positions['positions'].items()}
    orders_pos = {} 

    for k,v in usd_vals.items():
        if k in positions['positions']:
            orders_pos[k] = round(v-current_pos[k][0] if positions['positions'][k]['size'] > 0 else v+current_pos[k][0],2)
        else:
            orders_pos[k] = v
    # print(orders_pos)

    orders = []
    for symbol, order in orders_pos.items():
        side = True if order > 0 else False
        mid_price = float(markets[symbol]) + 0.05 if side else float(markets[symbol]) - 0.05
        if abs(order) > 10:
            orders.append(
                        {
                            "coin": symbol,
                            "is_buy": side,
                            "sz": round(abs(order) / mid_price,2),
                            "limit_px": round(mid_price,2),
                            "order_type": {"limit": {"tif": "Gtc"}},
                            "reduce_only": False,
                        }
                )
    for x in orders: print(f"{'Buying' if x['is_buy'] else 'Selling'} {x['coin']} {x['sz']} @ {x['limit_px']}")

    o.oms.bulk_orders(orders)

config = utils.get_config()
account: LocalAccount = eth_account.Account.from_key(config["secret_key"])
info = Info(constants.TESTNET_API_URL, skip_ws=True)
# Change this address to a vault that you lead
vault = None #"0xe0f75462a7ec115736207d647fa146395de88335"


# weights = {'SOL':-.7, 'AVAX':-.3, 'ETH':1}
# value = 2500

# for i in range(24):
#     o = OMS(config, account, vault)

#     rebalance(weights = weights, value = value)
#     time.sleep(60*60)

spreads = { 'SOL': {'buy':(0.05, 0.1), 'sell':(0.02, 0.05), 'inventory':2000},
            'ETH': {'buy':(0.02, 0.03), 'sell':(0.02, 0.05), 'inventory':2500},
            'AVAX': {'buy':(0.01, 0.02), 'sell':(0.03, 0.4), 'inventory':800},
           
            }

# for k,v in spreads.items():
#     v['inventory'] = abs(weights[k] * value)
# print(spreads)
o = OMS(config, account, vault)
# get_positions()
print(get_open_orders())
# asyncio.run(mm(spreads))

# import ccxt
import time
from concurrent.futures import ThreadPoolExecutor, thread
import concurrent.futures
# from matplotlib.pyplot import axis
from numpy import size
import os
from termcolor import colored
import pandas as pd
from prettytable import PrettyTable

import json

import eth_account


from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

def setup(vault_address=None,base_url=None, skip_ws=False):
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)
    account: LocalAccount = eth_account.Account.from_key(config["secret_key"])
    address = config.get("account_address")
    if address == "" or address == None:
        address = account.address
    print("Running with account address:", address)
    if address != account.address:
        print("Running with agent address:", account.address)
    info = Info(base_url, skip_ws)
    user_state = info.user_state(address)
    margin_summary = user_state["marginSummary"]
    if float(margin_summary["accountValue"]) == 0:
        print("Not running the example because the provided account has no equity.")
        url = info.base_url.split(".", 1)[1]
        error_string = f"No accountValue:\nIf you think this is a mistake, make sure that {address} has a balance on {url}.\nIf address shown is your API wallet address, update the config to specify the address of your account, not the address of the API wallet."
        raise Exception(error_string)
    if vault_address:
        print("Running with vault address:", vault_address)
        exchange = Exchange(account, base_url, vault_address=vault_address)
    else:
        exchange = Exchange(account, base_url, account_address=address)
    return address, info, exchange

class OMS:
    def __init__(self, vault):
        address, info, exchange = setup(vault, constants.MAINNET_API_URL, skip_ws=True)
        self.vault = vault
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.oms = Exchange(account, constants.MAINNET_API_URL, vault_address=vault)

        # meta = self.info.meta()
        # self.sz_decimals = {}
        # for asset_info in meta["universe"]:
        #     self.sz_decimals[asset_info["name"]] = asset_info["szDecimals"]

    def scale(self, rnd, price_range:tuple, num_orders:int):
        """
        price_range : Range of prices to be filled ex. (10,20)
        num_orders : number of orders
        """
        step = (price_range[1] - price_range[0]) / num_orders
        prices = list()
        for i in range(num_orders):
            value = price_range[0] + 2.75*i*step
            prices.append(round(value,int(rnd)))
            step -= step/num_orders
        return prices

    def buy_range(self, symbol:str, rnd, b_range:tuple, size:float, num_orders:int):
        """
        symbol : Symbol for market
        b_range: Buy range
        size : size to be filled
        num_orders : amount of orders to fill
        """
        buy = self.scale(rnd, b_range, num_orders=num_orders)
        unit_size = size / len(buy)

        for i, price in enumerate(buy):
            self.oms.order(coin=symbol, is_buy=True, sz = unit_size, limit_px=price, order_type={"limit": {"tif": "Gtc"}})
    
    def sell_range(self, symbol, rnd, s_range, size, num_orders):
        """
        symbol : Symbol for market
        s_range: Sell range
        size : size to be filled
        num_orders : amount of orders to fill
        """
        sell = self.scale(rnd, s_range, num_orders=num_orders)
        unit_size = size / len(sell)
        for i, price in enumerate(sell):
            self.oms.order(coin=symbol, is_buy=False, sz = unit_size, limit_px=price, order_type={"limit": {"tif": "Gtc"}})

    def equal_range(self, symbol, mid_price, pct_dev, size, num_orders):
        """
        symbol : Symbol for market
        mid_price : Mid price
        pct_dev : Percentage deviation
        size : size to be filled
        num_orders : amount of orders to fill
        """
        self.create_grid(symbol, 5,
                    	((mid_price*(1+pct_dev), mid_price*(1+(2*pct_dev)))) , 
                        ((mid_price*(1-pct_dev), mid_price*(1-(2*pct_dev)))), 
                        size, 
                        num_orders)

    def range(self, side, rnd, symbol, range, size, num_orders):
        scale = self.scale(rnd, range, num_orders=num_orders)
        unit_size = size / len(scale)
        orders = []
        for i, price in enumerate(scale):
            orders.append({
                            'coin':symbol, 
                           'is_buy':side, 
                           'sz' :unit_size, 
                           'limit_px':price, 
                           'order_type':{"limit": {"tif": "Gtc"}},
                           "reduce_only": False,
                           })
        return orders

    def cancel_all_orders(self, symbol):
        """
        symbol : Symbol for market
        """
        vault_bool = False
        if self.vault:
            vault_bool = True
            open_orders = self.info.open_orders(self.vault)
        else:
            open_orders = self.info.open_orders(self.address)

        coins = [i['coin'] for i in open_orders if i['coin'] == symbol]
        open_orders = [i['oid'] for i in open_orders if i['coin'] == symbol]

        self.cancel_orders(coins, open_orders)
        # check if any remaining ordersxs
        if vault_bool: open_orders = self.info.open_orders(self.vault)
        else:  open_orders = self.info.open_orders(self.address)
        if open_orders:
            self.cancel_all_orders(symbol=symbol)

        print("cancelled all orders for", symbol)

    def cancel_orders(self, coins, open_orders):
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self.oms.cancel, coins, open_orders)
        return list(results)


    def create_grid(self, symbol, rnd, sell_range, buy_range, size, num_orders):
        """
        symbol : Symbol for market
        sell_range: Sell range
        buy_range: Buy range
        size : size to be filled
        num_orders : amount of orders to fill
        """

        buy_orders = self.range(True, rnd, symbol, buy_range, int(size/2), int(num_orders/2))
        sell_orders = self.range(False, rnd, symbol, sell_range, int(size/2), int(num_orders/2))
        buy_resp = self.oms.bulk_orders(buy_orders)
        sell_resp = self.oms.bulk_orders(sell_orders)
        if buy_resp['status'] == 'ok':
            print(symbol, "buys submitted")
        if sell_resp['status'] == 'ok':
            print(symbol, "sells submitted")

    def bulk(self, orders):
        print(self.oms.bulk_orders(orders))

    def bulk_modify(self, modify_orders):
        self.oms.bulk_modify_orders_new(modify_orders)
    def get_open_orders(self):
        user = self.account.address if self.vault is None else self.vault
        return self.info.open_orders(user)

    def tighten_orders(self, coin, bump):
        bumped_orders = []
        for order in self.get_open_orders(): 
            if order['coin'] == coin:
                bumped_order = {
                    "oid": order['oid'],
                    "order": {
                        "coin": order['coin'],
                        "is_buy": order['side'] == 'B',
                        "sz": float(order['sz']),
                        "limit_px": float(order['limitPx'])+bump if order['side'] == 'A' else float(order['limitPx'])-bump,
                        "order_type": {"limit": {"tif": "Gtc"}},
                        "reduce_only": False
                    }
                }
                bumped_orders.append(bumped_order)
                
        self.bulk_modify(bumped_orders)

    def bump(self, coin, bump, side):
        # "SOL", 0.1, 'B'
        # bump by side
        # get open orders
        # for coin + side 
            # bump
        # submit
        bumped_orders = []
        for order in self.get_open_orders(): 
            if order['coin'] == coin:
                print(order['side'])
                if side == order['side']:
                    
                    new_price = float(order['limitPx'])-bump if order['side'] == 'A' else float(order['limitPx'])+bump
                    print(order['limitPx'], new_price)
                    bumped_order = {
                        "oid": order['oid'],
                        "order": {
                            "coin": order['coin'],
                            "is_buy": order['side'] == 'B',
                            "sz": float(order['sz']),
                            "limit_px": new_price,
                            "order_type": {"limit": {"tif": "Gtc"}},
                            "reduce_only": False
                        }
                    }
                    bumped_orders.append(bumped_order)
                
                
        self.bulk_modify(bumped_orders)



    def balance(self):
        df = pd.DataFrame(self.oms.fetch_balance()['info']['result'])
        sum = 0
        for i in df['usdValue']:
            sum += float(i)
        return sum

    def bid_ask(self, markets):
        mkts = pd.DataFrame(self.oms.fetch_markets())
        bid_ask = dict()
        for i in markets:
            s = i + "/USD:USD"
            last = mkts.query("symbol == @s")
            bid_ask[i] = (last['info'].iloc[0]['bid'], last['info'].iloc[0]['ask'])
        return bid_ask

    def chase_limit(self, markets):
        bid_ask = self.bid_ask(markets)
        print(bid_ask)

    def last_prices(self, markets):
        mkts = pd.DataFrame(self.oms.fetch_markets())

        last_prices = dict()
        for i in markets.keys():
            s = i + "/USD:USD"
            last = mkts.query("symbol == @s")
            # print(last['info'].iloc[0]['last'])
            last_prices[i] = (last['info'].iloc[0]['last'], last['info'].iloc[0]['minProvideSize'])
        return last_prices

    def twap_df(self, df):
        def side(row):
            if row['diff'] <= 0:
                return "sell"
            else:
                return "buy"

        duration = int(input("wait time between orders in seconds: "))
        orders = int(input("orders: "))
        df['unit_size'] = df['diff'].div(orders)
        df['side'] = df.apply(lambda row: side(row), axis=1)
        print(list(df.ticker))

        executed_orders = 0
        while executed_orders < orders:
            for i in df.iterrows():
                # print(i[1])
                color = "red" if i[1]['side'] == "sell" else "green"
                
                print(colored(f"{i[1]['side']}ing", color), colored(round(abs(i[1]['unit_size']),4), "cyan"), colored(i[1]['ticker'] + "-PERP" ,"yellow"))
                self.oms.create_market_order(symbol=i[1]['ticker'] + "-PERP", side=i[1]['side'], amount=abs(i[1]['unit_size']))
            executed_orders += 1
            time.sleep(duration)

    def twap(self, side:str, symbol:str, size:float, duration:int, orders:int = 20):
        """
        side : side to fill - "buy" or "sell"
        symbol : Symbol for market
        size : size to be filled
        duration : time to fill size in minutes
        orders : amount of orders to fill
        """
        # splits total_size into equal sizes to fill in given duration
        unit_size = size / orders
        sleep_duration = duration / orders * 60
        executed_orders = 0
        color = "red" if side=="sell" else "green"
        while executed_orders < orders:
            print(colored(f"{side}ing", color), colored(symbol,"yellow"), "size", colored(unit_size, "cyan"))
            self.oms.create_market_order(symbol=symbol, side=side, amount=unit_size)
            executed_orders += 1
            time.sleep(sleep_duration)

        print(f"{side} twap for {size} {symbol} completed")

    def ls_pair(self):
        """
        buy_symbol : Symbol to buy
        sell_symbol : Symbol to sell
        buy_size : Buy size to be filled
        sell_size : Sell size to be filled
        duration : time to fill size in minutes
        orders : amount of orders to fill
        """
        buy_symbol, buy_size = input("Ticker to long: ") + "-PERP", input("Size to long: ")
        sell_symbol, sell_size = input("Ticker to short: ") + "-PERP", input("Size to long: ")
        duration, orders = input("How long to twap in minutes: "), input("Number of orders: ")


        print(f"twapping into {buy_symbol} / {sell_symbol} for {duration} minutes")
        thread_list = []
        def buy():
            self.twap(side="buy", symbol=buy_symbol, size=buy_size, duration=duration, orders=orders)
        def sell():
            self.twap(side="sell", symbol=sell_symbol, size=sell_size, duration=duration, orders=orders)

        with ThreadPoolExecutor(max_workers=2) as executor:
            thread_list.append(executor.submit(buy))
            thread_list.append(executor.submit(sell))

    def reduce(self, symbol, pct):
        pass

    def ls_index(self, weights={}):
        sz = input(f"# of tickers: ")
        total_notional = float(input(f"Total Notional to enter ($): "))
        duration = int(input("Duration to enter (Minutes): "))
        orders = int(input("Total number of orders: "))
        if len(weights) == 0:
            for i in range(int(sz)):
                symbol = input("Ticker: ")
                weight = float(input("Weight: "))
                weights[symbol.upper()+"-PERP"] = weight

        sleep_duration = duration / orders * 60
        executed_orders = 0
        while executed_orders < orders:
            markets = self.oms.load_markets()

            for symbol, weight in weights.items():
                value = ((weight * total_notional) / orders) / round(float(markets[symbol[:-5]+"/USD"]['info']['price']),8)
                size_increment = float(markets[symbol[:-5]+"/USD"]['info']['sizeIncrement'])
                size = int(value / size_increment) * size_increment
                side = "buy" if weight > 0 else "sell"
                color = "red" if side=="sell" else "green"
                print(colored(f"{side}ing", color), colored(symbol,"yellow"), "size", colored(size, "cyan"))
                self.oms.create_market_order(symbol=symbol, side=side, amount=abs(size))
            executed_orders += 1
            if executed_orders == orders:
                print("index entry complete")
                return
            time.sleep(sleep_duration)

    def buy_percentage(self, symbol):
        print(self.oms.fetch_orders(symbol=symbol))

    def fetch_account_balance(self):
        balance = self.oms.fetch_balance()
        balances = [[i['coin'],i['usdValue']]for i in balance['info']['result'] if float(i['usdValue']) > 0.01]
        return sum([round(float(i[1]),2) for i in balances])

    def positions(self):
        t = PrettyTable(['Symbol', 'Side', 'Weight (%)', 'Contracts', 'Notional ($)', 'uPnL'])

        positions = pd.DataFrame(self.oms.fetch_positions())
        p = positions[positions['notional'] > 0][['symbol','notional','side','contracts','unrealizedPnl']]
        total = p['notional'].sum()
        p['weight'] = round(p['notional'] / total,2) * 100
        for i in p.sort_values(by=["weight"], ascending=False).iterrows():
            color = "red" if i[1]['side'] == "short" else "green"
            pnl = "red" if i[1]['unrealizedPnl'] <= 0 else "green"
            t.add_row([colored(i[1]['symbol'].removesuffix('/USD:USD'), 'yellow'), colored(i[1]['side'], color), colored(i[1]['weight'],"yellow"), colored(i[1]['contracts'], 'yellow'), colored(i[1]['notional'],"yellow"),  colored(i[1]['unrealizedPnl'], pnl)])
        account_value = self.fetch_account_balance()
        print(t)
        print(colored(f"Total Leverage: {total / account_value}", "yellow"))
        print(colored(f"Total $: {total}", "yellow"))
        return p

    def pnl(self):
        positions = pd.DataFrame(self.oms.fetch_positions())
        p = positions[positions['notional'] > 0][['symbol','notional','side','unrealizedPnl']]
        pnl = p['unrealizedPnl'].sum()
        return pnl, p

    def scale_tranches(self, side:str, symbol:str, ranges:list, size:float, orders_per_tranche:int, total_tranches:int):
        tranche_spread = abs(ranges[0] - ranges[1]) / total_tranches
        tranche = list()
        start_range = ranges[0]
        for i in range(total_tranches):

            if (side == "buy"):
                end_range = start_range-tranche_spread
            else:
                end_range = start_range+tranche_spread
            tranche.append([start_range, end_range])
            start_range = end_range
        for tranche_range in tranche:
            self.range(side, symbol, tranche_range, size/total_tranches, orders_per_tranche)

    def net_lev(self):
        net_lev = 0.0
        value = self.balance()
        pos = self.positions()
        for i in pos.iterrows():
            if i[1]['side'] == "short":
                net_lev -= i[1]['notional'] / value
            else:
                net_lev += i[1]['notional'] / value
        print("Net Leverage :", net_lev)

    def rebalance(self, markets={}):
        # rebalance account to weights portfolio, if empty ask user for input
        
        if markets=={}:
            sz = input("Number of tickers: ")
            for i in range(int(sz)):
                ins = input("Ticker: ")
                w = float(input("Weight: "))
                markets[ins.upper()] = w

        pos = self.positions()
        # pos = o.positions()
        lev = float(input("Leverage: "))
        lp = self.last_prices(markets)
        value = self.balance()
        size = dict()

        # calculate desired size
        for k,v in markets.items():
            notional = v*value*lev            
            amt = notional / float(lp[k][0])
            sz = int(amt / float(lp[k][1])) * float(lp[k][1])
            size[k] = sz

        sz_pd = pd.DataFrame([[k,v] for k,v in size.items()], columns=["ticker","size"])

        def size(row):
            if row['side'] == "short":
                return -row['contracts']
            else:
                return row['contracts']

        def rm_suffix(row):
            return row['symbol'].removesuffix("/USD:USD")

        curr = pd.DataFrame()
        if pos.size != 0:
            pos['curr_size'] = pos.apply (lambda row: size(row), axis=1)
            pos['ticker'] = pos.apply (lambda row: rm_suffix(row), axis=1)
            curr['curr_size'] = pos.apply (lambda row: size(row), axis=1)
            curr['ticker'] = pos.apply (lambda row: rm_suffix(row), axis=1)

        final = pd.DataFrame()
        if curr.size != 0:
            final = pd.merge(sz_pd, curr, on="ticker", how="outer").fillna(0)
            final['diff'] = final['size'] - final['curr_size']
            self.twap_df(final)
        else:
            final['ticker'] = sz_pd['ticker']
            final['diff'] = sz_pd['size']
            self.twap_df(final)
        self.net_lev()
        # print(pos.apply (lambda row: size(row), axis=1))


    def get_positions(self):
        response = self.info.user_state(self.vault)   


        coins = {i['position']['coin']: (float(i['position']['positionValue']), float(i['position']['szi'])) for i in response['assetPositions']}
        
        return {
            'positions' : coins,
            'marginSummary' : (float(response['marginSummary']['accountValue']), float(response['marginSummary']['totalNtlPos']))
        }

    def hl_get_candles(self, symbol, interval, lookback_minutes):
        candles = self.info.candles_snapshot(symbol, interval, int(time.time()*1000-(lookback_minutes*60000)), int(time.time()*1000))
        candle_df = pd.DataFrame([[i['t'], i['s'], i['c']] for i in candles], columns=['time', 'symbol', 'close'])
        return candle_df

    def execute_desired_coins(self, desired_coins, last_mids):
        for coin, sz in desired_coins.items():
            usd_price = round(float(f"{(last_mids[coin]):.5g}"), 6)
            if sz < 0 and abs(sz*usd_price) > 10:
                print(f"placing order for {coin} of sz {sz} with price {usd_price}")
                result=self.oms.order(coin, False, abs(round(sz, self.szMap[coin])), usd_price, {"limit": {"tif": "Gtc"}})
            elif sz > 0 and (sz*usd_price) > 10:
                print(f"placing order for {coin} of sz {sz} with price {usd_price}")
                result=self.oms.order(coin, True, abs(round(sz, self.szMap[coin])), usd_price, {"limit": {"tif": "Gtc"}})
            else:
                print("not placing order for", coin, sz*usd_price, "order value")
                result = {'response': {'data': {'statuses': ["OK"]}}}

            if 'error' in result['response']['data']['statuses'][0]:
                print("error placing order: ", result['response']['data']['statuses'][0]['error'])
    
    def hl_rebalance(self, markets, max_size):
        """
        param: markets : dictionary of tickers and weights
        param: max_size : max size of position
        param: range : % of range while rebalancing
        1. get current position
        2. get last price
        3. calculate size
        4. submit orders of top of book till balance is reached

        We want the sum of the weights to equal 0
        - sum of longs = sum of shorts = 1

        Example: {'kPEPE': 1, 'ETH': -.7, 'LDO': -.3}
        Max Size = 200
        Size gets divided amongst long and shorts
            - kPEPE : 1 -> LONG $100
            - ETH : -.7 -> SHORT $70
            - LDO : -.3  -> SHORT $30

        On a rebalance interval, we will check how far away the pair has deviated from the target weights
        and execute orders to bring it to the desired weights

        """
        min_order_size = 10
        pos = self.get_positions()
        last_mids = {ticker:float(last_mid) for ticker, last_mid in self.all_mids().items() if ticker in markets or ticker in pos['positions']}

        def sign(val):
            return 1 if val > 0 else -1
        
        current_amounts_usd = {
            ticker : (pos['positions'][ticker][0] * sign(pos['positions'][ticker][1])) for ticker in pos['positions']
        }

        # open orders
        open_orders = [{'coin': i['coin'],
                        'oid': i['oid']} for i in self.info.open_orders(self.vault)]
        if open_orders:
            print("cancelling open orders")
            self.oms.bulk_cancel(open_orders)


        # Desired Positions
        desired_usd = {coin: weight * max_size/2 for coin, weight in markets.items()}
        for coin in current_amounts_usd.keys():
            if coin not in desired_usd:
                desired_usd[coin] = 0

        for coin, weight in markets.items():
            if weight * max_size/2 // min_order_size > 0:
                desired_usd[coin] = weight * max_size/2
        
        # Subtract current positions from desired coins
        for coin,value in desired_usd.items():
            if coin in current_amounts_usd:
                desired_usd[coin] -= current_amounts_usd[coin]    

        # others
        for coin,value in current_amounts_usd.items():
            if coin not in desired_usd:
                desired_usd[coin] -= value

        desired_coins = {coin: round(amount / last_mids[coin], self.szMap[coin]) for coin, amount in desired_usd.items()}
        
        # Orders
        self.execute_desired_coins(desired_coins, last_mids)



"""
For each symbol we have 4 orders scaled on both sides of the book a configurable % away
We submit these orders as a batch and have them randomly expire and replaced over a period
of configured time. We also have a 

"""


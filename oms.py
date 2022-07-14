import ccxt
import time
from concurrent.futures import ThreadPoolExecutor, thread
import concurrent.futures
from numpy import size
import os
from termcolor import colored
import pandas as pd
from prettytable import PrettyTable
import colorama
colorama.init()

class OMS:
    def __init__(self):
        self.ftx =  ccxt.ftx({
                            'apiKey': "uEOKam46Pb2fkE5mOb3sM3T0P-054s2mZ2jx2UQD",
                            'secret': "Tjlu48nTBE8hSDHkm7thbE6BIjqOXhJkejgZlt45",
                        })

    def scale(self, price_range:tuple, num_orders:int):
        """
        price_range : Range of prices to be filled ex. (10,20)
        num_orders : number of orders
        """
        step = (price_range[1] - price_range[0]) / num_orders
        prices = list()
        for i in range(num_orders):
            value = price_range[0] + 2.75*i*step
            prices.append(value)
            step -= step/num_orders
        return prices

    def buy_range(self, symbol:str, b_range:tuple, size:int, num_orders:int):
        """
        symbol : Symbol for market
        b_range: Buy range 
        size : size to be filled
        num_orders : amount of orders to fill
        """
        buy = self.scale(b_range, num_orders=num_orders)
        unit_size = size / len(buy)
        for i, price in enumerate(buy):
            self.ftx.create_order(symbol=symbol, side="buy", amount = unit_size, type="takeProfit", price=price, params={"triggerPrice":price})

    def sell_range(self, symbol, s_range, size, num_orders):
        """
        symbol : Symbol for market
        s_range: Sell range 
        size : size to be filled
        num_orders : amount of orders to fill
        """
        sell = self.scale(s_range, num_orders=num_orders)
        unit_size = size / len(sell)
        for i, price in enumerate(sell):
            self.ftx.create_order(symbol=symbol, side="sell", amount = unit_size, type="takeProfit", price=price, params={"triggerPrice":price})
    
    def range(self, side, symbol, range, size, num_orders):
        scale = self.scale(range, num_orders=num_orders)
        unit_size = size / len(scale)
        for i, price in enumerate(scale):
            self.ftx.create_order(symbol=symbol, side=side, amount = unit_size, type="takeProfit", price=price, params={"triggerPrice":price})

    def cancel_all_orders(self, symbol):
        """
        symbol : Symbol for market
        """
        self.ftx.cancel_all_orders( symbol, {'conditionalOrdersOnly': 'true'})
        
    def create_grid(self, symbol, sell_range, buy_range, size, num_orders):
        """
        symbol : Symbol for market
        sell_range: Sell range 
        buy_range: Buy range 
        size : size to be filled
        num_orders : amount of orders to fill
        """
        
        self.range("buy", symbol, buy_range, int(size/2), int(num_orders/2))
        self.range("sell", symbol, sell_range, int(size/2), int(num_orders/2))

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
            self.ftx.create_market_order(symbol=symbol, side=side, amount=unit_size, price=None)
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
            markets = self.ftx.load_markets()

            for symbol, weight in weights.items():
                value = ((weight * total_notional) / orders) / round(float(markets[symbol[:-5]+"/USD"]['info']['price']),8)
                size_increment = float(markets[symbol[:-5]+"/USD"]['info']['sizeIncrement'])
                size = int(value / size_increment) * size_increment
                side = "buy" if weight > 0 else "sell"
                color = "red" if side=="sell" else "green"
                print(colored(f"{side}ing", color), colored(symbol,"yellow"), "size", colored(size, "cyan"))
                self.ftx.create_market_order(symbol=symbol, side=side, amount=abs(size), price=None)
            executed_orders += 1
            if executed_orders == orders:
                print("index entry complete")
                return
            time.sleep(sleep_duration)
            
    def buy_percentage(self, symbol):
        print(self.ftx.fetch_orders(symbol=symbol))

    def bump(self, ticker, bump_value):
        # get trigger orders of ticker
        # submit modified query with bump
        pass

    def fetch_account_balance(self):
        balance = self.ftx.fetch_balance()
        balances = [[i['coin'],i['usdValue']]for i in balance['info']['result'] if float(i['usdValue']) > 0.01]
        # print(sum([round(float(i[1]),2) for i in balances]))
        return sum([round(float(i[1]),2) for i in balances])


    def positions(self):
        t = PrettyTable(['Symbol', 'Side', 'Weight (%)', 'Contracts', 'Notional ($)', 'uPnL'])

        positions = pd.DataFrame(self.ftx.fetch_positions())
        p = positions[positions['notional'] > 0][['symbol','notional','side','contracts','unrealizedPnl']]
        total = p['notional'].sum()
        p['weight'] = round(p['notional'] / total * 100,2)
        for i in p.sort_values(by=["weight"], ascending=False).iterrows():
            color = "red" if i[1]['side'] == "short" else "green"
            pnl = "red" if i[1]['unrealizedPnl'] <= 0 else "green"
            t.add_row([colored(i[1]['symbol'].removesuffix('/USD:USD'), 'yellow'), colored(i[1]['side'], color), colored(i[1]['weight'],"yellow"), colored(i[1]['contracts'], 'yellow'), colored(i[1]['notional'],"yellow"),  colored(i[1]['unrealizedPnl'], "yellow")])
        account_value = self.fetch_account_balance()
        print(t)
        print(colored(f"Total Leverage: {total / account_value}", "yellow"))
        print(colored(f"Total $: {total}", "yellow"))

    

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
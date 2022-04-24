import ccxt
import time
from concurrent.futures import ThreadPoolExecutor, thread

from numpy import size

class OMS:
    def __init__(self):
        self.ftx =  ccxt.ftx({
                            'apiKey': 'fcEEkmTziv-l20a7szD_R8U7V-kq-YMFn9d7LuCF',
                            'secret': 'xF5rfQJU6evo75SYu1Ous64_axyOIm-Z-TyJzVeL',
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
    
    def range(self, side, symbol, s_range, size, num_orders):
        scale = self.scale(s_range, num_orders=num_orders)
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
        unit_size = size / (2*num_orders)
        sell_range = self.scale(sell_range, num_orders)
        buy_range = self.scale(buy_range, num_orders)
        for i, price in enumerate(sell_range):
            if i % 2 == 1:
                self.ftx.create_order(symbol=symbol, side="sell", amount = unit_size, type="limit", price=price, params={})
            else:
                self.ftx.create_order(symbol=symbol, side="sell", amount = unit_size, type="takeProfit", price=price, params={"triggerPrice":price})
            
            
        for i, price in enumerate(buy_range):
            if i % 2 == 1:
                self.ftx.create_order(symbol=symbol, side="buy", amount = unit_size, type="limit", price=price, params={})
            else:
                self.ftx.create_order(symbol=symbol, side="buy", amount = unit_size, type="takeProfit", price=price, params={"triggerPrice":price})

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
        while executed_orders < orders:
            self.ftx.create_market_order(symbol=symbol, side=side, amount=unit_size)
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
            
    def ls_index(self, weights={}):
        sz = len(weights)
        if sz == 0:
            weights = dict()
            for i in range(sz):
                ticker = input(f"ticker #{i}: ")
                weight = input(f"weight #{i}: ")
                weights[ticker] = weight
            

    def bump(self, ticker, bump_value):
        # get trigger orders of ticker
        # submit modified query with bump


    
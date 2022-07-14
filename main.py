import sys
sys.path.append("..")
from oms import OMS
import os
import argparse
from termcolor import colored

parser = argparse.ArgumentParser()
parser.add_argument("function", help="function to execute")


args = parser.parse_args()
o = OMS()
functions = ["rebalance","cancel_all", "twap", "positions", "ls_pair", "index", "grid","scale", "tranche"]
helper = ["rebalances portfolio", "cancels all orders for symbol", "twaps into specified pair", "prints current positions", "enter into l/s pair with twap", "enter into multiweighted index","creates grid on specified instrument","scales into orders", "places scaled tranches"]
match args.function:
	case "help":
		d = {functions[i]:helper[i] for i in range(len(functions))}
		for k,v in d.items():
			print(colored(k, "red"), "-", colored(v,"green"))
	case "login":
		if os.getenv('API_KEY') == "" or os.getenv("API_SECRET"):
			os.environ["API_KEY"] = input("Insert API Key: ")
			os.environ["API_SECRET"] = input("Insert API SECRET: ")
		else:
			print("Already logged in!")
	case "cancel_all":
		symbol = input("Symbol to cancel: ")
		o.cancel_all_orders(symbol)
	case "twap":
		side = input("Side to enter: ")
		symbol = input("Symbol to enter: ")
		size = float(input("Size to enter (in symbol): "))
		duration = int(input("duration to buy (in minutes): "))
		orders = int(input("Total orders to execute: "))
		o.twap(side, symbol, size, duration, orders)
	case "positions":
		o.positions()
	case "ls_pair":
		o.ls_pair()
	case "grid":
		symbol = input("Symbol to enter: ")
		start_range = float(input("SELL - Start Range: "))
		end_range = float(input("SELL - End Range: "))
		b_start_range = float(input("BUY - Start Range: "))
		b_end_range = float(input("BUY - End Range: "))
		size = float(input("Size to enter (in symbol): "))
		orders = int(input("Total orders to execute: "))
		o.create_grid(symbol, [start_range, end_range], [b_start_range, b_end_range], size, orders)
	case "index":
		o.ls_index()
	case "scale":
		side = input("Side to enter: ")
		symbol = input("Symbol to enter: ")
		start_range = float(input("Start Range: "))
		end_range = float(input("End Range: "))
		size = float(input("Size to enter (in symbol): "))
		orders = int(input("Total orders to execute: "))
		o.range(side, symbol, [start_range, end_range], size, orders)
	case "rebalance":
		o.rebalance()
	case "tranche":
		side = input("Side to enter: ")
		symbol = input("Symbol to enter: ")
		start_range = float(input("Start Range: "))
		end_range = float(input("End Range: "))
		size = float(input("Size to enter (in symbol): "))
		orders_per_tranche = int(input("orders per tranche: "))
		total_tranches = int(input("total tranches: "))
		o.scale_tranches(side, symbol, [start_range, end_range], size, orders_per_tranche, total_tranches)
import sys
sys.path.append("..")
from oms import OMS

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("function", help="function to execute")


args = parser.parse_args()
o = OMS()
functions = ["cancel_all", "twap", "ls_pair", "index", "scale", "tranche"]
helper = ["cancels all orders for symbol", "twaps into specified pair", "enter into l/s pair with twap", "enter into multiweighted index","scales into orders", "places scaled tranches"]
match args.function:
	case "help":
		d = {functions[i]:helper[i] for i in range(len(functions))}
		for k,v in d.items():
			print(f"{k} - {v}")
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
	case "ls_pair":
		o.ls_pair()
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
	case "tranche":
		side = input("Side to enter: ")
		symbol = input("Symbol to enter: ")
		start_range = float(input("Start Range: "))
		end_range = float(input("End Range: "))
		size = float(input("Size to enter (in symbol): "))
		orders_per_tranche = int(input("orders per tranche: "))
		total_tranches = int(input("total tranches: "))
		o.scale_tranches(side, symbol, [start_range, end_range], size, orders_per_tranche, total_tranches)
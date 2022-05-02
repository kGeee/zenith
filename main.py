import sys
sys.path.append("..")
from oms import OMS

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("function", help="function to execute")


args = parser.parse_args()
o = OMS()
match args.function:
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
	case "ls":
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
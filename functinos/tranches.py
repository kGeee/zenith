import sys, getopt
sys.path.append("..")
from oms import OMS

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("side", help="side to enter tranche")
parser.add_argument("symbol", help="symbol to enter")
parser.add_argument("start_range", help="start of range")
parser.add_argument("end_range", help="end of range")
parser.add_argument("size", help="total size to enter")
parser.add_argument("orders_per_tranche", help="orders per tranche")
parser.add_argument("total_tranches", help="total number of tranches to enter")

args = parser.parse_args()

o = OMS()
o.scale_tranches(args.side, args.symbol, [float(args.start_range), float(args.end_range)], float(args.size), int(args.orders_per_tranche), int(args.total_tranches))

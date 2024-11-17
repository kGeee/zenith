import streamlit as st
import pandas as pd
import time
from oms import OMS

def plot_account_value(line_chart):
    account_value_file = "data/account_value.csv"
    data = pd.read_csv(account_value_file, header=None)
    data.columns = ['Account Value']
    print(data['Account Value'][-10:])
    line_chart.line_chart(data['Account Value'][-10:])

def append_new():
    account_value_file = "data/account_value.csv"
    o = OMS(vault="0x19ee977043c0ddc263d30ef7054272cead8dd763")
    value = o.info.user_state(o.vault)['marginSummary']['accountValue']
    st.write(value)
    with open(account_value_file, 'a') as f:
         f.write(f"{value}\n")

def main():
    st.title('Account Value Plotter')
    line_chart = st.empty()
    plot_account_value(line_chart)
    while True:
        append_new()
        plot_account_value(line_chart)
        time.sleep(10)

if __name__ == '__main__':
    main()



account_value_file = "data/account_value.csv"
while True:
	with open(account_value_file, 'a') as f:
		f.write(f"{o.info.user_state(o.vault)['marginSummary']['accountValue']}\n")
	time.sleep(10)
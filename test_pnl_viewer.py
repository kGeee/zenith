import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from oms import OMS

def main():
    st.title("PnL Plot Refresh")

    # Inputs
    weights = st.text_input("Weights", value="SOL:0.33,BTC:0.33,INJ:-0.5,kPEPE:0.33,DOGE:-0.5")
    lookback_minutes = st.slider("Lookback Minutes", 1, 60, 10)
    initial_size = st.slider("Initial Size", 100, 1000, 250)

    # Weights dictionary
    weights_dict = {}
    for pair in weights.split(","):
        symbol, weight = pair.split(":")
        weights_dict[symbol] = float(weight)

    # Add ticker to weights dictionary
    add_ticker = st.button("Add Ticker")
    if add_ticker:
        new_ticker = st.text_input("New Ticker")
        new_weight = st.number_input("Weight", value=0.0)
        if st.button("Add"):
            weights_dict[new_ticker] = new_weight
            weights = ",".join([f"{k}:{v}" for k, v in weights_dict.items()])

    # Refresh button
    if st.button("Refresh"):
        # Calculate PnL
        o = OMS(vault="0x19ee977043c0ddc263d30ef7054272cead8dd763")
        total_df = pd.DataFrame()
        for symbol in weights_dict.keys():
            df = o.hl_get_candles(symbol, '1m', lookback_minutes)
            total_df = pd.concat([total_df, df])

        df_wide = total_df.pivot(index='time', columns='symbol', values='close')
        for i in weights_dict.keys():
            df_wide[i] = pd.to_numeric(df_wide[i])

        init_map = {i: initial_size * weights_dict[i] / float(df_wide[i].iloc[0]) for i in weights_dict.keys()}
        for k, v in weights_dict.items():
            df_wide[f'{k}USD'] = df_wide[k].mul(init_map[k])

        columns = [f'{k}USD' for k in weights_dict.keys()]
        pnl = pd.DataFrame({'pnl': df_wide[columns].sum(axis=1)})

        # Display PnL plot
        st.line_chart(pnl['pnl'])

if __name__ == "__main__":
    main()
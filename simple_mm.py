import sys
sys.path.append("..")
from oms import OMS
import time
import streamlit as st


st.title('Hyperliquid Rebalancer')
num_pairs = st.slider('Number of Pairs', min_value=1, max_value=10, value=1)
pairs = {}
for i in range(num_pairs):
    # Get the key and value for the pair
    key = st.text_input(f'Pair {i+1}')
    value = st.number_input(f'Value {i+1}', value=0.0)
    
    # Add the pair to the dictionary
    pairs[key] = value

vault = st.text_input('Vault Address', value="0x19ee977043c0ddc263d30ef7054272cead8dd763")
amount = st.number_input('Amount in USD', value=200)
if st.button('Rebalance'):
    o = OMS(vault=vault)

    o.hl_rebalance(pairs,amount)
    
    # {'WIF':0.33, 
    #                 'kBONK': 0.33, 
    #                 'kFLOKI':0.33,
    #                 'kPEPE': .25,
    #                 'DOGE': -1}
# while True:
#     mid = float(o.all_mids()[symbol])
#     if mid != mid_cache: 
#         mid_cache = mid
#         o.cancel_all_orders(symbol)
#         o.equal_range(symbol, mid, pct_dev, max_size, num_orders)
#         print(f"waiting for {wait_time_in_seconds} seconds")
#         time.sleep(wait_time_in_seconds)

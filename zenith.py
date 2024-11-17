import streamlit as st
from oms import OMS

st.title('OMS Functions Demo')

# Initialize OMS object
config = {...}  # Provide the necessary configuration
account = {...}  # Provide the necessary account information
vault = {...}  # Provide the necessary vault information
oms = OMS(config, account, vault)

# Function 1
st.subheader('Function 1')
rnd_input = st.number_input('Enter input for rnd', value=0)
symbol_input = st.text_input('Enter symbol', value='default')
b_range_input = st.text_input('Enter b_range', value='default')
size_input = st.number_input('Enter size', value=0)
num_orders_input = st.number_input('Enter num_orders', value=0)

if st.button('Run Function 1'):
    buy = oms.scale(rnd_input, (b_range_input.split(',')), num_orders_input)
    st.write('Result for Function 1:', buy)

# Function 2
st.subheader('Function 2')
s_range_input = st.text_input('Enter s_range', value='default')

if st.button('Run Function 2'):
    sell = oms.scale(rnd_input, (s_range_input.split(',')), num_orders_input)
    st.write('Result for Function 2:', sell)

# Function 3
st.subheader('Function 3')
side_input = st.text_input('Enter side', value='default')
range_input = st.text_input('Enter range', value='default')

if st.button('Run Function 3'):
    scale = oms.scale(rnd_input, (range_input.split(',')), num_orders_input)
    st.write('Result for Function 3:', scale)
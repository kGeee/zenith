import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# Streamlit UI components
st.title('Crypto Portfolio Historical Returns')
start_date = st.date_input('Start Date', value=pd.to_datetime('2020-01-01'))
end_date = st.date_input('End Date', value=pd.to_datetime('2023-01-01'))

crypto_weights = {
    'BTC-USD': st.slider('Bitcoin Weight', 0.0, 1.0, 0.4),
    'ETH-USD': st.slider('Ethereum Weight', 0.0, 1.0, 0.3),
    'ADA-USD': st.slider('Cardano Weight', 0.0, 1.0, 0.2),
    'SOL-USD': st.slider('Solana Weight', 0.0, 1.0, 0.1)
}

if st.button('Fetch Data and Plot'):
    # Fetch historical data
    data = {}
    for crypto in crypto_weights.keys():
        data[crypto] = yf.download(crypto, start=start_date, end=end_date)['Adj Close']

    # Combine the data into a single DataFrame
    df = pd.DataFrame(data)

    # Calculate daily returns
    daily_returns = df.pct_change().dropna()

    # Calculate portfolio returns
    weights = np.array(list(crypto_weights.values()))
    portfolio_returns = daily_returns.dot(weights)

    # Calculate cumulative returns
    cumulative_returns = (1 + portfolio_returns).cumprod()

    # Plot the cumulative returns
    st.line_chart(cumulative_returns)
    for crypto in crypto_weights.keys():
        st.line_chart((1 + daily_returns[crypto]).cumprod(), label=crypto)

    st.success('Data fetched and plotted successfully!')

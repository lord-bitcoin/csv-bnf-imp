import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Function to load the uploaded CSV file
def load_data(uploaded_file):
    data = pd.read_csv(uploaded_file, skiprows=6, delimiter=',', on_bad_lines='skip')
    data['Amount Fiat'] = pd.to_numeric(data['Amount Fiat'], errors='coerce')
    data['Amount Asset'] = pd.to_numeric(data['Amount Asset'], errors='coerce')
    data['Asset market price'] = pd.to_numeric(data['Asset market price'], errors='coerce')
    data['Fee'] = pd.to_numeric(data['Fee'], errors='coerce')
    data['Tax Fiat'] = pd.to_numeric(data['Tax Fiat'], errors='coerce')
    return data

# Streamlit app starts here
st.title("Bitcoin Trading Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
if uploaded_file is not None:
    data = load_data(uploaded_file)

    # Sidebar input for BTC holdings and current value
    st.sidebar.header("BTC Analysis")
    current_btc_holding = st.sidebar.number_input("Current BTC Holding", value=0.5)
    current_btc_value = st.sidebar.number_input("Current BTC Value (EUR)", value=100000)

    # Filter BTC data
    btc_data = data[data['Asset'] == 'BTC']

    btc_bought = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Asset'].sum()
    btc_bought_cost = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Fiat'].sum()

    btc_sold = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Asset'].sum()
    btc_sold_revenue = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Fiat'].sum()

    btc_remaining = btc_bought - btc_sold
    total_btc_value = current_btc_holding * current_btc_value

    # Calculate profits
    realized_profit = btc_sold_revenue - (btc_sold / btc_bought * btc_bought_cost) if btc_bought > 0 else 0
    unrealized_profit = total_btc_value - (btc_remaining / btc_bought * btc_bought_cost) if btc_bought > 0 else 0

    # Display data and results
    st.header("Transaction Data")
    st.dataframe(data.head())

    st.header("Summary Metrics")
    st.write(f"**Total BTC Bought:** {btc_bought:.6f} BTC")
    st.write(f"**Total BTC Sold:** {btc_sold:.6f} BTC")
    st.write(f"**BTC Remaining:** {btc_remaining:.6f} BTC")
    st.write(f"**Realized Profit:** {realized_profit:.2f} EUR")
    st.write(f"**Unrealized Profit:** {unrealized_profit:.2f} EUR")

    # Plot data
    st.header("Visualizations")

    # Top assets by total fiat value
    asset_summary = data.groupby('Asset').agg(
        Total_Fiat=('Amount Fiat', 'sum'),
        Total_Asset=('Amount Asset', 'sum')
    ).sort_values(by='Total_Fiat', ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(asset_summary.index, asset_summary['Total_Fiat'])
    ax.set_title("Top 10 Assets by Fiat Value", fontsize=16)
    ax.set_xlabel("Asset", fontsize=14)
    ax.set_ylabel("Total Fiat Value (EUR)", fontsize=14)
    st.pyplot(fig)

    # Transaction type summary
    transaction_summary = data.groupby('Transaction Type').agg(
        Total_Fiat=('Amount Fiat', 'sum'),
        Transaction_Count=('Transaction ID', 'count')
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(transaction_summary.index, transaction_summary['Total_Fiat'])
    ax.set_title("Total Fiat Value by Transaction Type", fontsize=16)
    ax.set_xlabel("Transaction Type", fontsize=14)
    ax.set_ylabel("Total Fiat Value (EUR)", fontsize=14)
    st.pyplot(fig)
else:
    st.info("Please upload a CSV file to begin.")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Function to load the uploaded CSV file
def load_data(uploaded_file):
    errors = []
    try:
        data = pd.read_csv(uploaded_file, skiprows=6, delimiter=',', on_bad_lines='skip')
        data['Amount Fiat'] = pd.to_numeric(data['Amount Fiat'], errors='coerce')
        data['Amount Asset'] = pd.to_numeric(data['Amount Asset'], errors='coerce')
        data['Asset market price'] = pd.to_numeric(data['Asset market price'], errors='coerce')
        data['Fee'] = pd.to_numeric(data['Fee'], errors='coerce')
        data['Tax Fiat'] = pd.to_numeric(data['Tax Fiat'], errors='coerce')
        # Convert Timestamp column to datetime
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
        # Create Year column
        data['Year'] = data['Timestamp'].dt.year
        return data, errors
    except Exception as e:
        errors.append(str(e))
        return pd.DataFrame(), errors

# Function to calculate realized profit using FIFO method
def calculate_realized_profit_fifo(btc_data):
    buys = btc_data[btc_data['Transaction Type'] == 'buy'][['Amount Asset', 'Amount Fiat']].values.tolist()
    sells = btc_data[btc_data['Transaction Type'] == 'sell'][['Amount Asset', 'Amount Fiat']].values.tolist()

    realized_profit = 0
    for sell_amount, sell_fiat in sells:
        while sell_amount > 0 and buys:
            buy_amount, buy_fiat = buys[0]
            if sell_amount >= buy_amount:
                realized_profit += sell_fiat - buy_fiat
                sell_amount -= buy_amount
                buys.pop(0)
            else:
                realized_profit += sell_fiat - (sell_amount / buy_amount) * buy_fiat
                buys[0][0] -= sell_amount
                sell_amount = 0
    return realized_profit

# Streamlit app starts here
st.title("Bitcoin Trading Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
if uploaded_file is not None:
    data, errors = load_data(uploaded_file)

    if errors:
        st.warning(f"Errors encountered during file processing: {', '.join(errors)}")
    
    if not data.empty:
        # Sidebar input for BTC holdings and current value
        st.sidebar.header("BTC Analysis")
        current_btc_holding = st.sidebar.number_input("Current BTC Holding", value=0.5, min_value=0.0, step=0.1)
        current_btc_value = st.sidebar.number_input("Current BTC Value (EUR)", value=100000, min_value=0)

        # Filter BTC data
        btc_data = data[data['Asset'] == 'BTC']

        btc_bought = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Asset'].sum()
        btc_bought_cost = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Fiat'].sum()

        btc_sold = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Asset'].sum()
        btc_sold_revenue = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Fiat'].sum()

        btc_remaining = btc_bought - btc_sold
        total_btc_value = current_btc_holding * current_btc_value

        # Calculate profits using FIFO
        realized_profit = calculate_realized_profit_fifo(btc_data)
        unrealized_profit = total_btc_value - (btc_remaining / btc_bought * btc_bought_cost) if btc_bought > 0 else 0

        # Calculate taxes
        flat_tax = realized_profit * 0.30  # Flat Tax (30%)
        progressive_tax = realized_profit * 0.11 if realized_profit <= 10000 else realized_profit * 0.30

        # Group data by year
        yearly_summary = data.groupby('Year').agg(
            Total_Bought=('Amount Asset', 'sum'),
            Total_Sold=('Amount Fiat', 'sum'),
            Transactions=('Timestamp', 'count')
        )

        # Tabs for navigation
        tab1, tab2, tab3 = st.tabs(["Résumé", "Transactions Data", "Graphiques"])

        with tab1:
            st.header("Summary Metrics")
            st.write(f"**Total BTC Bought:** {btc_bought:.6f} BTC")
            st.write(f"**Total BTC Sold:** {btc_sold:.6f} BTC")
            st.write(f"**BTC Remaining:** {btc_remaining:.6f} BTC")
            st.write(f"**Realized Profit:** {realized_profit:.2f} EUR")
            st.write(f"**Unrealized Profit:** {unrealized_profit:.2f} EUR")
            st.write(f"**Flat Tax:** {flat_tax:.2f} EUR")
            st.write(f"**Progressive Tax (approx):** {progressive_tax:.2f} EUR")

            st.subheader("Yearly Summary")
            st.dataframe(yearly_summary)

        with tab2:
            st.header("Transaction Data")
            st.dataframe(data)

        with tab3:
            st.header("Visualizations")

            # Profit evolution graph by year
            fig, ax = plt.subplots(figsize=(10, 6))
            yearly_summary['Total_Bought'].plot(kind='bar', ax=ax, label='Total Bought')
            yearly_summary['Total_Sold'].plot(kind='bar', ax=ax, label='Total Sold', alpha=0.7, color='orange')
            ax.set_title("Yearly Trading Summary", fontsize=16)
            ax.set_xlabel("Year", fontsize=14)
            ax.set_ylabel("Amount", fontsize=14)
            ax.legend()
            st.pyplot(fig)

else:
    st.info("Please upload a CSV file to begin.")

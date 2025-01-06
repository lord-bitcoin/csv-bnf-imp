import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Function to load the uploaded CSV file
def load_data(uploaded_file):
    errors = []
    try:
        data = pd.read_csv(uploaded_file, skiprows=6, delimiter=',', on_bad_lines='skip')
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Year'] = data['Date'].dt.year  # Extract fiscal year
        data['Amount Fiat'] = pd.to_numeric(data['Amount Fiat'], errors='coerce')
        data['Amount Asset'] = pd.to_numeric(data['Amount Asset'], errors='coerce')
        data['Asset market price'] = pd.to_numeric(data['Asset market price'], errors='coerce')
        data['Fee'] = pd.to_numeric(data['Fee'], errors='coerce')
        data['Tax Fiat'] = pd.to_numeric(data['Tax Fiat'], errors='coerce')
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

# Function to export data grouped by fiscal years to Excel
def export_to_excel_by_year(data):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for year, group in data.groupby('Year'):
            group.to_excel(writer, index=False, sheet_name=str(year))
    output.seek(0)
    return output

# Streamlit app starts here
st.title("Bitcoin Trading Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
if uploaded_file is not None:
    data, errors = load_data(uploaded_file)

    if errors:
        st.warning(f"Errors encountered during file processing: {', '.join(errors)}")
    
    if not data.empty:
        st.success(f"File loaded successfully: {uploaded_file.name}")

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

        # Tabs for navigation
        tab1, tab2, tab3, tab4 = st.tabs(["Résumé", "Transactions Data", "Graphiques", "Export Excel"])

        with tab1:
            st.header("Summary Metrics")
            st.write(f"**Total BTC Bought:** {btc_bought:.6f} BTC")
            st.write(f"**Total BTC Sold:** {btc_sold:.6f} BTC")
            st.write(f"**BTC Remaining:** {btc_remaining:.6f} BTC")
            st.write(f"**Realized Profit:** {realized_profit:.2f} EUR")
            st.write(f"**Unrealized Profit:** {unrealized_profit:.2f} EUR")
            st.write(f"**Flat Tax:** {flat_tax:.2f} EUR")
            st.write(f"**Progressive Tax (approx):** {progressive_tax:.2f} EUR")

        with tab2:
            st.header("Transaction Data")
            st.dataframe(data)

        with tab3:
            st.header("Visualizations")

            # Top assets by total fiat value
            asset_summary = data.groupby('Asset').agg(
                Total_Fiat=('Amount Fiat', 'sum'),
                Total_Asset=('Amount Asset', 'sum')
            ).sort_values(by='Total_Fiat', ascending=False).head(10)

            fig1, ax1 = plt.subplots(figsize=(10, 6))
            ax1.bar(asset_summary.index, asset_summary['Total_Fiat'])
            ax1.set_title("Top 10 Assets by Fiat Value", fontsize=16)
            ax1.set_xlabel("Asset", fontsize=14)
            ax1.set_ylabel("Total Fiat Value (EUR)", fontsize=14)
            for i, v in enumerate(asset_summary['Total_Fiat']):
                ax1.text(i, v + 100, f"{v:.2f}", ha='center')
            st.pyplot(fig1)

            # Profit evolution graph
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            ax2.plot(["Realized", "Unrealized"], [realized_profit, unrealized_profit], marker='o')
            ax2.set_title("Profit Evolution", fontsize=16)
            ax2.set_ylabel("EUR", fontsize=14)
            for i, v in enumerate([realized_profit, unrealized_profit]):
                ax2.text(i, v + 100, f"{v:.2f}", ha='center')
            st.pyplot(fig2)

        with tab4:
            st.header("Export Data by Fiscal Year")
            excel_data = export_to_excel_by_year(data)
            st.download_button(
                label="Download Excel File (by Fiscal Year)",
                data=excel_data,
                file_name="Transactions_By_Fiscal_Year.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.warning("No valid data found in the file.")
else:
    st.info("Please upload a CSV file to begin.")

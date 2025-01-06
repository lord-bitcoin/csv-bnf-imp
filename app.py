import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

def load_data(uploaded_file):
    errors = []
    try:
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file, skiprows=6, delimiter=',', on_bad_lines='skip')
        elif uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            errors.append("Unsupported file format. Please upload a CSV or Excel file.")
            return pd.DataFrame(), errors

        data['Amount Fiat'] = pd.to_numeric(data['Amount Fiat'], errors='coerce')
        data['Amount Asset'] = pd.to_numeric(data['Amount Asset'], errors='coerce')
        data['Asset market price'] = pd.to_numeric(data['Asset market price'], errors='coerce')
        data['Fee'] = pd.to_numeric(data['Fee'], errors='coerce')
        data['Tax Fiat'] = pd.to_numeric(data['Tax Fiat'], errors='coerce')
        return data, errors
    except Exception as e:
        errors.append(str(e))
        return pd.DataFrame(), errors

def convert_to_excel(data):
    output = BytesIO()
    data.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output

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

st.title("Bitcoin Trading Analysis")

uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])
if uploaded_file is not None:
    data, errors = load_data(uploaded_file)

    if errors:
        st.warning(f"Errors encountered during file processing: {', '.join(errors)}")

    if not data.empty:
        st.sidebar.header("BTC Analysis")
        current_btc_holding = st.sidebar.number_input("Current BTC Holding", value=0.5, min_value=0.0, step=0.1)
        current_btc_value = st.sidebar.number_input("Current BTC Value (EUR)", value=100000, min_value=0)

        btc_data = data[data['Asset'] == 'BTC']

        btc_bought = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Asset'].sum()
        btc_bought_cost = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Fiat'].sum()

        btc_sold = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Asset'].sum()
        btc_sold_revenue = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Fiat'].sum()

        btc_remaining = btc_bought - btc_sold
        total_btc_value = current_btc_holding * current_btc_value

        realized_profit = calculate_realized_profit_fifo(btc_data)
        unrealized_profit = total_btc_value - (btc_remaining / btc_bought * btc_bought_cost) if btc_bought > 0 else 0

        flat_tax = realized_profit * 0.30
        progressive_tax = realized_profit * 0.11 if realized_profit <= 10000 else realized_profit * 0.30

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

        with tab2:
            st.header("Transaction Data")
            st.dataframe(data)

            st.markdown("### Export Transactions Data to Excel")
            excel_data = convert_to_excel(data)
            st.download_button(
                label="Download Excel File",
                data=excel_data,
                file_name="transactions_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with tab3:
            st.header("Visualizations")

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

            fig2, ax2 = plt.subplots(figsize=(10, 6))
            ax2.plot(["Realized", "Unrealized"], [realized_profit, unrealized_profit], marker='o')
            ax2.set_title("Profit Evolution", fontsize=16)
            ax2.set_ylabel("EUR", fontsize=14)
            for i, v in enumerate([realized_profit, unrealized_profit]):
                ax2.text(i, v + 100, f"{v:.2f}", ha='center')
            st.pyplot(fig2)
else:
    st.info("Please upload a CSV or Excel file to begin.")

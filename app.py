import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Function to load the uploaded CSV file
def load_data(uploaded_file):
    errors = []
    try:
        data = pd.read_csv(uploaded_file, skiprows=6, delimiter=',', quotechar='"', on_bad_lines='skip')
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce', utc=True)
        data['Amount Fiat'] = pd.to_numeric(data['Amount Fiat'], errors='coerce')
        data['Amount Asset'] = pd.to_numeric(data['Amount Asset'], errors='coerce')
        data['Asset market price'] = pd.to_numeric(data['Asset market price'], errors='coerce')
        data['Fee'] = pd.to_numeric(data['Fee'], errors='coerce')
        data['Tax Fiat'] = pd.to_numeric(data['Tax Fiat'], errors='coerce')
        return data, errors
    except Exception as e:
        errors.append(str(e))
        return pd.DataFrame(), errors

# Function to filter data by selected years
def filter_data_by_year(data, selected_years):
    if 'Timestamp' in data.columns:
        return data[data['Timestamp'].dt.year.isin(selected_years)]
    return data

# Streamlit app starts here
st.title("Bitcoin Trading Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
if uploaded_file is not None:
    data, errors = load_data(uploaded_file)

    if errors:
        st.warning(f"Errors encountered during file processing: {', '.join(errors)}")
    
    if not data.empty:
        # Sidebar input for year selection
        st.sidebar.header("Filter by Year")
        available_years = sorted(data['Timestamp'].dt.year.dropna().unique())
        selected_years = st.sidebar.multiselect("Select years", available_years, default=available_years)

        # Filter data by selected years
        filtered_data = filter_data_by_year(data, selected_years)

        # Sidebar input for BTC holdings and current value
        st.sidebar.header("BTC Analysis")
        current_btc_holding = st.sidebar.number_input("Current BTC Holding", value=0.5, min_value=0.0, step=0.1)
        current_btc_value = st.sidebar.number_input("Current BTC Value (EUR)", value=100000, min_value=0)

        # Filter BTC data
        btc_data = filtered_data[filtered_data['Asset'] == 'BTC']

        btc_bought = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Asset'].sum()
        btc_bought_cost = btc_data[btc_data['Transaction Type'] == 'buy']['Amount Fiat'].sum()

        btc_sold = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Asset'].sum()
        btc_sold_revenue = btc_data[btc_data['Transaction Type'] == 'sell']['Amount Fiat'].sum()

        btc_remaining = btc_bought - btc_sold
        total_btc_value = current_btc_holding * current_btc_value

        # Calculate realized and unrealized profits
        realized_profit = btc_sold_revenue - (btc_bought_cost * (btc_sold / btc_bought)) if btc_bought > 0 else 0
        unrealized_profit = total_btc_value - (btc_remaining / btc_bought * btc_bought_cost) if btc_bought > 0 else 0

        # Calculate taxes
        flat_tax = realized_profit * 0.30  # Flat Tax (30%)
        progressive_tax = realized_profit * 0.11 if realized_profit <= 10000 else realized_profit * 0.30

        # Tabs for navigation
        tab1, tab2, tab3 = st.tabs(["Summary", "Transactions Data", "Visualizations"])

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
            st.dataframe(filtered_data)

            # Export to Excel
            st.markdown("### Export Transactions Data to Excel")
            output = BytesIO()
            filtered_data.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.download_button(
                label="Download Excel File",
                data=output,
                file_name="filtered_transactions_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with tab3:
            st.header("Visualizations")

            # Top assets by total fiat value
            asset_summary = filtered_data.groupby('Asset').agg(
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

else:
    st.info("Please upload a CSV file to begin.")

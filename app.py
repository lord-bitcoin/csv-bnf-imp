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

# Function to calculate PRUG
def calculate_prug(data):
    prug_history = []
    total_asset = 0
    total_cost = 0
    realized_profits = []

    for _, row in data.iterrows():
        if row['Transaction Type'] == 'buy':
            total_asset += row['Amount Asset']
            total_cost += row['Amount Fiat']
        elif row['Transaction Type'] == 'sell':
            prug = total_cost / total_asset if total_asset > 0 else 0
            realized_profit = row['Amount Fiat'] - (row['Amount Asset'] * prug)
            total_asset -= row['Amount Asset']
            total_cost -= row['Amount Asset'] * prug
            realized_profits.append({
                'Transaction ID': row['Transaction ID'],
                'Amount Sold': row['Amount Asset'],
                'Sale Revenue': row['Amount Fiat'],
                'PRUG': prug,
                'Realized Profit': realized_profit
            })
            prug_history.append({
                'Remaining Asset': total_asset,
                'Remaining Cost': total_cost,
                'Updated PRUG': total_cost / total_asset if total_asset > 0 else 0
            })

    return realized_profits, prug_history

# Streamlit app starts here
st.title("Bitcoin Trading Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
if uploaded_file is not None:
    data = load_data(uploaded_file)

    # Filter BTC data
    btc_data = data[data['Asset'] == 'BTC']
    
    # Add PRUG Tab
    tab1, tab2, tab3, tab4 = st.tabs(["Résumé", "Transactions Data", "Graphiques", "PRUG"])

    with tab1:
        st.header("Summary Metrics")
        # Existing summary code here...

    with tab2:
        st.header("Transaction Data")
        st.dataframe(data.head())

    with tab3:
        st.header("Visualizations")
        # Existing visualization code here...

    with tab4:
        st.header("PRUG Analysis")

        realized_profits, prug_history = calculate_prug(btc_data)
        
        if realized_profits:
            st.subheader("Realized Profits")
            st.dataframe(pd.DataFrame(realized_profits))

        if prug_history:
            st.subheader("PRUG History")
            st.dataframe(pd.DataFrame(prug_history))
else:
    st.info("Please upload a CSV file to begin.")

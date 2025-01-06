import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Function to load the uploaded Excel file
def load_data(uploaded_file):
    errors = []
    try:
        data = pd.read_excel(uploaded_file, engine='openpyxl')
        data['Amount Fiat'] = pd.to_numeric(data['Amount Fiat'], errors='coerce')
        data['Amount Asset'] = pd.to_numeric(data['Amount Asset'], errors='coerce')
        data['Asset market price'] = pd.to_numeric(data['Asset market price'], errors='coerce')
        data['Fee'] = pd.to_numeric(data['Fee'], errors='coerce')
        data['Tax Fiat'] = pd.to_numeric(data['Tax Fiat'], errors='coerce')
        # Ensure 'Date' column is in datetime format
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        return data, errors
    except Exception as e:
        errors.append(str(e))
        return pd.DataFrame(), errors

# Streamlit app starts here
st.title("Bitcoin Trading Analysis - Excel Only")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type="xlsx")
if uploaded_file is not None:
    data, errors = load_data(uploaded_file)

    if errors:
        st.warning(f"Errors encountered during file processing: {', '.join(errors)}")
    
    if not data.empty:
        # Filter BTC data
        btc_data = data[data['Asset'] == 'BTC']

        # Sort data by year if 'Date' column exists
        if 'Date' in data.columns:
            data['Year'] = data['Date'].dt.year
            sorted_data = data.sort_values(by='Year')
        else:
            sorted_data = data

        # Display sorted data
        st.header("Sorted Data by Year")
        st.dataframe(sorted_data)

        # Export to Excel
        st.markdown("### Export Sorted Transactions Data to Excel")
        output = BytesIO()
        sorted_data.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="Download Sorted Excel File",
            data=output,
            file_name="sorted_transactions_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Visualizations
        st.header("Visualizations")

        # Transactions by year (if 'Year' column exists)
        if 'Year' in sorted_data.columns:
            transactions_by_year = sorted_data.groupby('Year').size()
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(transactions_by_year.index, transactions_by_year.values)
            ax.set_title("Transactions by Year", fontsize=16)
            ax.set_xlabel("Year", fontsize=14)
            ax.set_ylabel("Number of Transactions", fontsize=14)
            st.pyplot(fig)

else:
    st.info("Please upload an Excel file to begin.")

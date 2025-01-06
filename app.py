import streamlit as st
import pandas as pd
from io import BytesIO

def convert_csv_to_excel(csv_file):
    """Convert uploaded CSV file to a formatted Excel file."""
    try:
        # Load CSV data
        csv_data = pd.read_csv(csv_file)

        # Clean metadata and extract transaction data (customize based on your file structure)
        if len(csv_data.columns) == 1:
            csv_data = pd.read_csv(csv_file, skiprows=6)

        # Check if Timestamp column exists
        if 'Timestamp' in csv_data.columns:
            # Add Year, Month, and Day columns
            csv_data['Timestamp'] = pd.to_datetime(csv_data['Timestamp'], errors='coerce', utc=True)
            csv_data['Year'] = csv_data['Timestamp'].dt.year
            csv_data['Month'] = csv_data['Timestamp'].dt.month
            csv_data['Day'] = csv_data['Timestamp'].dt.day

            # Remove timezone info from Timestamp
            csv_data['Timestamp'] = csv_data['Timestamp'].dt.tz_localize(None)
        else:
            st.warning("Timestamp column not found. Year, Month, and Day columns will not be added.")

        # Convert DataFrame to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            csv_data.to_excel(writer, index=False, sheet_name='Transactions')
        output.seek(0)
        return output
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Streamlit app
st.title("CSV to Formatted Excel Converter")

st.markdown("Upload a CSV file to convert it into a formatted Excel file.")

# File upload
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file is not None:
    with st.spinner("Processing your file..."):
        excel_file = convert_csv_to_excel(uploaded_file)
        if excel_file:
            st.success("File converted successfully!")

            # Provide download link for the Excel file
            st.download_button(
                label="Download Excel File",
                data=excel_file,
                file_name="formatted_transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

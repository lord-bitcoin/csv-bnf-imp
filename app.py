import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Function to load the uploaded CSV file
def load_data(uploaded_file):
    try:
        data = pd.read_csv(uploaded_file, skiprows=6, delimiter=',', on_bad_lines='skip')
        # Convert numeric columns
        data['Amount Fiat'] = pd.to_numeric(data['Amount Fiat'], errors='coerce')
        data['Amount Asset'] = pd.to_numeric(data['Amount Asset'], errors='coerce')
        data['Asset market price'] = pd.to_numeric(data['Asset market price'], errors='coerce')
        data['Fee'] = pd.to_numeric(data['Fee'], errors='coerce')
        data['Tax Fiat'] = pd.to_numeric(data['Tax Fiat'], errors='coerce')
        return data
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return None

# Streamlit app starts here
st.title("Bitcoin Trading Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
if uploaded_file is not None:
    data = load_data(uploaded_file)
    
    if data is not None:
        # Affiche les colonnes disponibles
        st.write("Colonnes disponibles :", list(data.columns))
        
        # Sélectionner la colonne des dates
        date_column = st.selectbox(
            "Sélectionnez la colonne contenant les dates :",
            options=data.columns,
            index=0  # Par défaut, sélectionne la première colonne
        )
        
        try:
            # Convertir la colonne sélectionnée en datetime
            data['Date'] = pd.to_datetime(data[date_column], errors='coerce')
            
            # Filtrer uniquement les transactions valides
            btc_data = data[data['Asset'] == 'BTC']
            btc_data['Year'] = btc_data['Date'].dt.year

            st.success("Données chargées avec succès.")
            
            # Tabs for navigation
            tab1, tab2, tab3 = st.tabs(["Résumé", "Transactions Data", "Graphiques"])

            with tab1:
                st.header("Résumé")
                
                # Get unique years in descending order
                unique_years = sorted(btc_data['Year'].dropna().unique(), reverse=True)
                
                # Create sub-tabs for each year
                year_tabs = st.tabs([str(year) for year in unique_years])
                
                for i, year in enumerate(unique_years):
                    with year_tabs[i]:
                        year_data = btc_data[btc_data['Year'] == year]
                        
                        btc_bought_year = year_data[year_data['Transaction Type'] == 'buy']['Amount Asset'].sum()
                        btc_bought_cost_year = year_data[year_data['Transaction Type'] == 'buy']['Amount Fiat'].sum()

                        btc_sold_year = year_data[year_data['Transaction Type'] == 'sell']['Amount Asset'].sum()
                        btc_sold_revenue_year = year_data[year_data['Transaction Type'] == 'sell']['Amount Fiat'].sum()

                        btc_remaining_year = btc_bought_year - btc_sold_year
                        realized_profit_year = (
                            btc_sold_revenue_year
                            - (btc_sold_year / btc_bought_year * btc_bought_cost_year)
                        ) if btc_bought_year > 0 else 0
                        
                        # Display metrics for the year
                        st.write(f"### Année {year}")
                        st.write(f"**BTC Acheté :** {btc_bought_year:.6f} BTC")
                        st.write(f"**BTC Vendu :** {btc_sold_year:.6f} BTC")
                        st.write(f"**BTC Restant :** {btc_remaining_year:.6f} BTC")
                        st.write(f"**Profit Réalisé :** {realized_profit_year:.2f} EUR")

            with tab2:
                st.header("Transaction Data")
                st.dataframe(data.head())

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
                st.pyplot(fig1)

                # Transaction type summary
                transaction_summary = data.groupby('Transaction Type').agg(
                    Total_Fiat=('Amount Fiat', 'sum'),
                    Transaction_Count=('Transaction ID', 'count')
                )

                fig2, ax2 = plt.subplots(figsize=(10, 6))
                ax2.bar(transaction_summary.index, transaction_summary['Total_Fiat'])
                ax2.set_title("Total Fiat Value by Transaction Type", fontsize=16)
                ax2.set_xlabel("Transaction Type", fontsize=14)
                ax2.set_ylabel("Total Fiat Value (EUR)", fontsize=14)
                st.pyplot(fig2)
        except Exception as e:
            st.error(f"Erreur lors du traitement des données : {e}")
else:
    st.info("Please upload a CSV file to begin.")

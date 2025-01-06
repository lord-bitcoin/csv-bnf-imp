import streamlit as st
import pandas as pd
import PyPDF2
import io

# Fonction pour extraire le texte d'un fichier PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Fonction pour traiter les données extraites
def process_data(data):
    # Diviser les données par lignes
    rows = data.split("\n")
    
    # Identifier les colonnes et les données correspondantes
    columns = [
        "Transaction ID", "Timestamp", "Transaction Type", "In/Out", "Amount Fiat", "Fiat", 
        "Amount Asset", "Asset", "Asset market price", "Asset market price currency", "Asset class", 
        "Product ID", "Fee", "Fee asset", "Spread", "Spread Currency", "Tax Fiat"
    ]

    # Filtrer les lignes contenant des transactions
    transactions = []
    for row in rows:
        # Diviser chaque ligne en colonnes
        row_data = row.split()
        
        # Vérifier si la ligne a suffisamment de colonnes
        if len(row_data) >= len(columns):
            transactions.append(row_data[:len(columns)])  # Garder uniquement le bon nombre de colonnes

    # Vérifier si des transactions valides ont été trouvées
    if not transactions:
        raise ValueError("Aucune transaction valide trouvée dans les données extraites.")

    # Convertir les transactions en DataFrame
    df = pd.DataFrame(transactions, columns=columns[:len(transactions[0])])
    
    # Convertir les colonnes numériques
    numeric_columns = ["Amount Fiat", "Amount Asset", "Asset market price", "Fee", "Spread", "Tax Fiat"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Ajouter une colonne "Year" et "Month"
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['Year'] = df['Timestamp'].dt.year
    df['Month'] = df['Timestamp'].dt.month

    return df

# Calcul des indicateurs demandés
def calculate_indicators(df):
    # Filtrer les transactions BTC
    btc_df = df[df['Asset'] == 'BTC']

    # Calculs
    total_btc_bought = btc_df[(btc_df['Transaction Type'] == 'buy') & (btc_df['In/Out'] == 'outgoing')]['Amount Asset'].sum()
    total_btc_sold = btc_df[(btc_df['Transaction Type'] == 'sell') & (btc_df['In/Out'] == 'incoming')]['Amount Asset'].sum()
    btc_remaining = total_btc_bought - total_btc_sold

    realized_profit_fifo = btc_df[btc_df['Transaction Type'] == 'sell']['Amount Fiat'].sum()
    unrealized_profit = btc_remaining * btc_df['Asset market price'].iloc[-1] if not btc_df.empty else 0

    flat_tax = realized_profit_fifo * 0.3  # Ajustable selon le taux de taxation
    progressive_tax = realized_profit_fifo * 0.15  # Exemple : approximation

    return {
        "Total BTC Bought (BTC)": total_btc_bought,
        "Total BTC Sold (BTC)": total_btc_sold,
        "BTC Remaining (BTC)": btc_remaining,
        "Realized Profit FIFO (EUR)": realized_profit_fifo,
        "Unrealized Profit (EUR)": unrealized_profit,
        "Flat Tax (EUR)": flat_tax,
        "Progressive Tax (EUR)": progressive_tax,
    }

# Interface Streamlit
st.title("Analyse des Transactions Bitcoin")

uploaded_file = st.file_uploader("Importer un fichier PDF", type="pdf")

if uploaded_file is not None:
    # Extraire le texte du PDF
    text_data = extract_text_from_pdf(uploaded_file)

    # Traiter les données
    try:
        df = process_data(text_data)

        # Afficher les données
        st.subheader("Transactions Filtrées")
        st.dataframe(df)

        # Calculer les indicateurs
        indicators = calculate_indicators(df)

        # Afficher les indicateurs
        st.subheader("Conclusions")
        for key, value in indicators.items():
            st.write(f"{key}: {value}")
    except ValueError as e:
        st.error(f"Erreur lors du traitement des données : {e}")

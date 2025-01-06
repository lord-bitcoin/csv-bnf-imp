import streamlit as st
import pandas as pd

# Titre de l'application
st.title("Transformation de Timestamp dans un fichier CSV")

# Téléchargement du fichier
uploaded_file = st.file_uploader("Téléversez un fichier CSV", type=["csv"])

if uploaded_file is not None:
    # Option pour indiquer le nombre de lignes à sauter
    skip_rows = st.number_input("Nombre de lignes à sauter (si nécessaire)", min_value=0, value=0)

    # Lecture du fichier CSV
    try:
        data = pd.read_csv(uploaded_file, skiprows=skip_rows)
        st.write("Aperçu des données chargées :", data)

        # Vérifiez si une colonne de timestamp est présente
        timestamp_col = st.selectbox(
            "Sélectionnez la colonne Timestamp", data.columns
        )

        # Transformer la colonne timestamp
        if timestamp_col:
            try:
                data[timestamp_col] = pd.to_datetime(data[timestamp_col], errors='coerce')
                data['Year'] = data[timestamp_col].dt.year
                data['Month'] = data[timestamp_col].dt.month
                data['Day'] = data[timestamp_col].dt.day

                st.write("Aperçu des données transformées :", data.head())

                # Bouton de téléchargement
                @st.cache_data
                def convert_df_to_csv(df):
                    return df.to_csv(index=False).encode('utf-8')

                csv = convert_df_to_csv(data)

                st.download_button(
                    label="Télécharger le fichier transformé",
                    data=csv,
                    file_name="transformed_data.csv",
                    mime="text/csv",
                )
            except Exception as e:
                st.error(f"Erreur lors de la transformation : {e}")
    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
else:
    st.info("Veuillez téléverser un fichier pour commencer.")

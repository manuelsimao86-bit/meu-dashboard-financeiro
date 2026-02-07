import streamlit as st
import pandas as pd
import pdfplumber  # Ferramenta para ler o PDF

# Função específica para extrair dados de extratos em PDF
def processar_pdf(file):
    all_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                all_data.extend(table)
    
    # Criar tabela (assume-se colunas: Data, Descrição, Valor)
    df_pdf = pd.DataFrame(all_data[1:], columns=all_data[0])
    return df_pdf

# Na parte do Upload do ficheiro:
uploaded_file = st.file_uploader("Carregue o seu ficheiro", type=["xlsx", "csv", "pdf"])

if uploaded_file:
    if uploaded_file.name.endswith('.pdf'):
        df = processar_pdf(uploaded_file)
        st.success("✅ PDF lido com sucesso!")
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    
    # Restante do seu código de análise (Gráficos, KPIs, etc.)
    st.write(df)

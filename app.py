import streamlit as st
import pandas as pd
import pdfplumber
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

# 1. Configuração da Página
st.set_page_config(page_title="FinAnalysis Angola PRO", layout="wide", page_icon="🇦🇴")

st.title("🇦🇴 FinAnalysis Angola | Gestão Sénior")
st.markdown("---")

# 2. Funções de Suporte (A Inteligência do Sistema)

def limpar_moeda(valor):
    """Converte strings de Kwanza (ex: 1.500,00) em números decimais."""
    if pd.isna(valor) or valor == "":
        return 0.0
    s = str(valor).strip().replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

def processar_pdf(file):
    """Lê tabelas de PDFs, ideal para Mapas de Amortização e Extratos."""
    dados_finais = []
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            tabela = pagina.extract_table()
            if tabela:
                dados_finais.extend(tabela)
    
    if not dados_finais:
        return pd.DataFrame()
    
    # Criar DataFrame e usar a primeira linha como cabeçalho
    df = pd.DataFrame(dados_finais[1:], columns=dados_finais[0])
    return df

# 3. Interface de Utilizador (Sidebar)
st.sidebar.header("Configurações")
uploaded_file = st.sidebar.file_uploader("Carregue Extrato ou Mapa (PDF, XLSX, CSV)", type=["pdf", "xlsx", "csv"])

# 4. Processamento de Dados
if uploaded_file:
    # Identificar tipo de ficheiro
    extensao = uploaded_file.name.split('.')[-1].lower()
    
    with st.spinner('A processar ficheiro...'):
        if extensao == 'pdf':
            df = processar_pdf(uploaded_file)
            st.success("✅ PDF lido com sucesso!")
        elif extensao == 'xlsx':
            df = pd.read_excel(uploaded_file)
            st.success("✅ Excel carregado!")
        else:
            df = pd.read_csv(uploaded_file)
            st.success("✅ CSV carregado!")

    # Verificar se o DataFrame tem dados
    if not df.empty:
        st.write("### 📋 Visualização de Dados Brutos")
        # Limpeza básica: remove colunas ou linhas totalmente vazias
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        st.dataframe(df, use_container_width=True)

        # 5. Análise de Valores (Tentativa Automática)
        st.markdown("---")
        st.write("### 📊 Análise Financeira Automática")
        
        # Tentar converter todas as colunas que parecem números
        for col in df.columns:
            if df[col].dtype == 'object':
                # Testa se a coluna tem números formatados como texto
                df[col + "_num"] = df[col].apply(limpar_moeda)
        
        # Filtrar apenas colunas que conseguimos converter em números reais
        df_numerico = df.select_dtypes(include=['number'])
        
        if not df_numerico.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Totais Calculados:**")
                st.write(df_numerico.sum())
            
            with col2:
                st.write("**Gráfico de Tendência:**")
                st.bar_chart(df_numerico.iloc[:, :2]) # Mostra as primeiras 2 colunas numéricas
        else:
            st.warning("Não foram detetadas colunas numéricas claras para gerar gráficos automáticos.")

        # 6. Exportação de Relatório
        st.sidebar.markdown("---")
        if st.sidebar.button("📑 Gerar Relatório PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "Relatório FinAnalysis Angola", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, f"Ficheiro analisado: {uploaded_file.name}", ln=True)
            pdf.cell(200, 10, f"Data da análise: {pd.Timestamp.now().strftime('%d/%m/%Y')}", ln=True)
            
            # Gerar o binário do PDF
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.sidebar.download_button("📥 Baixar Relatório", data=pdf_output, file_name="Relatorio_Angola.pdf")

    else:
        st.error("O ficheiro parece estar vazio ou não contém tabelas legíveis.")
else:
    st.info("Aguardando carregamento de ficheiro no menu lateral para iniciar a análise financeira.")

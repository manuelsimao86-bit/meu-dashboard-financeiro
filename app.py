import streamlit as st
import pandas as pd
import pdfplumber
import matplotlib.pyplot as plt

# 1. Configuração de Especialista
st.set_page_config(page_title="FinAnalysis Angola PRO", layout="wide", page_icon="🇦🇴")

st.title("🇦🇴 FinAnalysis Angola | Analista de Orçamento Familiar")
st.markdown("---")

# 2. Funções de Limpeza de Moeda (Kz)
def limpar_kwanza(valor):
    """Converte '1.500,00' ou '500,00' em números reais somáveis."""
    if pd.isna(valor) or valor == "" or str(valor).lower() == "none" or valor == "0":
        return 0.0
    # Remove pontos de milhares e troca vírgula por ponto
    s = str(valor).strip().replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

def categorizar_familiar(descricao):
    """Agrupa movimentos por palavras-chave comuns em Angola."""
    desc = str(descricao).upper()
    if any(p in desc for p in ["KERO", "SHOPRITE", "CANDANDO", "MAXI", "ALIMENTAR"]): return "🍎 Alimentação"
    if any(p in desc for p in ["UNITEL", "AFRICEL", "ZAP", "DSTV", "ENDE", "EPAL"]): return "🏠 Contas de Casa"
    if any(p in desc for p in ["RESTAURANTE", "CAFE", "LAZER", "CINEMA"]): return "🍹 Lazer"
    if any(p in desc for p in ["FARMACIA", "HOSPITAL", "CLINICA"]): return "⚕️ Saúde"
    if any(p in desc for p in ["AGT", "IRT", "IMPOSTO", "SEGURANCA SOCIAL"]): return "🏛️ Impostos & Taxas"
    if any(p in desc for p in ["ESCOLA", "FACULDADE", "PROPINAS"]): return "📚 Educação"
    if any(p in desc for p in ["SALARIO", "VENCIMENTO", "TRANSFERENCIA RECEBIDA"]): return "💰 Receitas"
    return "📦 Outros Movimentos"

# 3. Extração e Limpeza de Cabeçalho
def processar_pdf_bancario(file):
    dados = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tabela = page.extract_table()
            if tabela: dados.extend(tabela)
    if not dados: return pd.DataFrame()
    
    df_temp = pd.DataFrame(dados)
    # Procurar a linha que contém os títulos das colunas (Data/Descritivo/Débito)
    indice_inicio = 0
    for i, row in df_temp.iterrows():
        txt = " ".join(map(str, row.values)).lower()
        if 'débito' in txt or 'crédito' in txt or 'descritivo' in txt:
            indice_inicio = i
            break
            
    df = pd.DataFrame(dados[indice_inicio+1:], columns=dados[indice_inicio])
    return df

# 4. Interface Sidebar
st.sidebar.header("📁 Gestão de Extratos")
uploaded_file = st.sidebar.file_uploader("Carregue o PDF do Banco", type=["pdf"])

if uploaded_file:
    df = processar_pdf_bancario(uploaded_file)
    
    if not df.empty:
        # Mapeamento de colunas (Débito = Gastos, Crédito = Entradas)
        col_desc = ""
        for col in df.columns:
            nome = str(col).lower()
            if 'débito' in nome or 'debito' in nome: df['GASTOS'] = df[col].apply(limpar_kwanza)
            if 'crédito' in nome or 'credito' in nome: df['ENTRADAS'] = df[col].apply(limpar_kwanza)
            if 'descritivo' in nome or 'descrição' in nome: col_desc = col

        # Garantir que as colunas existem para não dar erro
        if 'GASTOS' not in df.columns: df['GASTOS'] = 0.0
        if 'ENTRADAS' not in df.columns: df['ENTRADAS'] = 0.0

        # Categorização
        df['Categoria'] = df[col_desc].apply(categorizar_familiar) if col_desc else "📦 Outros"

        # 5. DASHBOARD DE VALORES REAIS
        st.success("✅ Extrato Processado com Sucesso!")
        
        t_entradas = df['ENTRADAS'].sum()
        t_gastos = df['GASTOS'].sum()
        saldo = t_entradas - t_gastos
        
        c1, c2, c3 = st.columns(3)
        c1.metric("TOTAL DE ENTRADAS (Créditos)", f"{t_entradas:,.2f} Kz")
        c2.metric("TOTAL DE GASTOS (Débitos)", f"{t_gastos:,.2f} Kz")
        c3.metric("SALDO DO PERÍODO", f"{saldo:,.2f} Kz", delta=float(saldo))

        # 6. AGRUPAMENTO FAMILIAR
        st.markdown("---")
        st.subheader("👨‍👩‍👧‍👦 Resumo de Gastos Familiares por Grupo")
        
        resumo = df[df['GASTos'] > 0].groupby('Categoria')['GASTOS'].sum().sort_values(ascending=False)
        
        if not resumo.empty:
            col_t, col_g = st.columns([1, 1])
            with col_t:
                st.write("**Tabela de Totais por Categoria:**")
                st.table(resumo.map(lambda x: f"{x:,.2f} Kz"))
            with col_g:
                st.write("**Distribuição Percentual:**")
                fig, ax = plt.subplots()
                resumo.plot.pie(autopct='%1.1f%%', ax=ax, colors=plt.cm.Paired.colors)
                ax.set_ylabel('')
                st.pyplot(fig)

        st.markdown("---")
        st.write("#### 📋 Detalhe de Todos os Movimentos")
        st.dataframe(df.dropna(axis=1, how='all'), use_container_width=True)

else:
    st.info("Aguardando carregamento do extrato para análise familiar.")

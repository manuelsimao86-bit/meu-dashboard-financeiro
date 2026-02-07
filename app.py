import streamlit as st
import pandas as pd
import pdfplumber
import matplotlib.pyplot as plt

# 1. Configuração de Especialista
st.set_page_config(page_title="FinAnalysis Angola PRO", layout="wide", page_icon="🇦🇴")

st.title("🇦🇴 FinAnalysis Angola | Analista de Orçamento Familiar")
st.markdown("---")

# 2. Funções de Limpeza e Inteligência
def converter_kwanza(valor):
    if pd.isna(valor) or valor == "" or str(valor).lower() == "none":
        return 0.0
    s = str(valor).strip().replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

def categorizar_movimento(descricao):
    """Inteligência para agrupar movimentos familiares e profissionais em Angola."""
    desc = str(descricao).upper()
    
    if any(palavra in desc for palavra in ["KERO", "SHOPRITE", "CANDANDO", "MAXI", "SUPERMERCADO", "ALIMENTAR"]):
        return "🍎 Alimentação & Supermercado"
    elif any(palavra in desc for palavra in ["UNITEL", "AFRICEL", "ZAP", "DSTV", "INTERNET", "ENDE", "EPAL"]):
        return "🏠 Contas de Casa (Luz/Água/Tel)"
    elif any(palavra in desc for palavra in ["RESTAURANTE", "CAFE", "BAR", "LAZER", "CINEMA"]):
        return "🍹 Lazer & Restaurantes"
    elif any(palavra in desc for palavra in ["FARMACIA", "HOSPITAL", "CLINICA", "CENTRO MEDICO"]):
        return "⚕️ Saúde"
    elif any(palavra in desc for palavra in ["TAXA", "AGT", "IRT", "IMPOSTO", "SEGURANCA SOCIAL"]):
        return "🏛️ Impostos & Taxas AGT"
    elif any(palavra in desc for palavra in ["ESCOLA", "FACULDADE", "LIVRARIA", "COLEGIO", "PROPINAS"]):
        return "📚 Educação"
    elif any(palavra in desc for palavra in ["COMBUSTIVEL", "SONANGOL", "PUMA", "GASOLINA", "MECANICO"]):
        return "🚗 Transporte & Viatura"
    elif any(palavra in desc for palavra in ["SALARIO", "VENCIMENTO", "TRANSFERENCIA RECEBIDA", "HONORARIOS"]):
        return "💰 Receitas & Rendimentos"
    else:
        return "📦 Outros Gastos"

def processar_pdf_inteligente(file):
    dados = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tabela = page.extract_table()
            if tabela: dados.extend(tabela)
    if not dados: return pd.DataFrame()
    
    df_temp = pd.DataFrame(dados)
    # Localizar cabeçalho (Data/Descritivo)
    linha_mestre = 0
    for i, row in df_temp.iterrows():
        txt = " ".join(map(str, row.values)).lower()
        if 'data' in txt and ('descritivo' in txt or 'movimento' in txt):
            linha_mestre = i
            break
    
    df = pd.DataFrame(dados[linha_mestre+1:], columns=dados[linha_mestre])
    return df

# 3. Sidebar
st.sidebar.header("📁 Gestão de Documentos")
uploaded_file = st.sidebar.file_uploader("Carregue o Extrato Bancário", type=["pdf"])

if uploaded_file:
    df = processar_pdf_inteligente(uploaded_file)
    
    if not df.empty:
        # 4. Tratamento de Colunas
        col_desc = ""
        for col in df.columns:
            nome = str(col).lower()
            if 'débito' in nome or 'debito' in nome: df['DEBITO'] = df[col].apply(converter_kwanza)
            if 'crédito' in nome or 'credito' in nome: df['CREDITO'] = df[col].apply(converter_kwanza)
            if 'descritivo' in nome or 'descrição' in nome or 'movimento' in nome: col_desc = col

        # Aplicar Categorização
        if col_desc:
            df['Categoria'] = df[col_desc].apply(categorizar_movimento)
        else:
            df['Categoria'] = "📦 Outros Gastos"

        # 5. DASHBOARD PRINCIPAL
        st.success(f"✅ Análise do Extrato concluída com sucesso!")
        
        t_deb = df['DEBITO'].sum() if 'DEBITO' in df.columns else 0
        t_cre = df['CREDITO'].sum() if 'CREDITO' in df.columns else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("TOTAL DE ENTRADAS", f"{t_cre:,.2f} Kz")
        m2.metric("TOTAL DE GASTOS", f"{t_deb:,.2f} Kz")
        m3.metric("SALDO DISPONÍVEL", f"{(t_cre - t_deb):,.2f} Kz")

        # 6. AGRUPAMENTO FAMILIAR (O seu pedido)
        st.markdown("---")
        st.subheader("👨‍👩‍👧‍ internal Resumo de Gastos Familiares")
        
        if 'DEBITO' in df.columns:
            # Agrupar apenas os débitos por categoria
            resumo_familiar = df[df['DEBITO'] > 0].groupby('Categoria')['DEBITO'].sum().sort_values(ascending=False)
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.write("**Gastos por Grupo:**")
                st.table(resumo_familiar.map(lambda x: f"{x:,.2f} Kz"))
            
            with c2:
                fig, ax = plt.subplots()
                resumo_familiar.plot.pie(autopct='%1.1f%%', ax=ax, cmap='viridis')
                ax.set_ylabel('')
                st.pyplot(fig)

        st.markdown("---")
        st.write("#### 📋 Lista Detalhada com Categorias")
        st.dataframe(df.dropna(axis=1, how='all'), use_container_width=True)

else:
    st.info("Por favor, carregue o extrato PDF para ver o agrupamento de despesas.")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ========== CONFIGURAÇÃO GERAL ==========
st.set_page_config(page_title="📊 Dashboard Epidemiológico", layout="wide")

st.title("📊 Dashboard Epidemiológico Interativo")
st.caption("Fonte: Google Sheets - Atualização automática")

# Dicionário para padronizar nomes de colunas que vieram com acento ou espaço
COLUNA_MAP = {
    'SEMANA EPIDEMIOLÓGICA 2': 'SEMANA_EPIDEMIOLOGICA',
    'DATA DE NOTIFICAÇÃO': 'DATA_NOTIFICACAO',
    'DATA PRIMEIRO SINTOMAS': 'DATA_SINTOMAS',
    'FA': 'FAIXA_ETARIA',
    'BAIRRO RESIDÊNCIA': 'BAIRRO',
    'EVOLUÇÃO DO CASO': 'EVOLUCAO',
    'CLASSIFCAÇÃO': 'CLASSIFICACAO_FINAL',
    # Incluindo outras colunas relevantes
    'RAÇA/COR': 'RACA_COR',
    'ESCOLARIDADE': 'ESCOLARIDADE',
    'DISTRITO': 'DISTRITO'
}


# ========= FUNÇÃO DE CARREGAR DADOS =========
@st.cache_data
def carregar_dados():
    # URL de EXPORTAÇÃO (correta) da sua planilha
    url = "https://docs.google.com/spreadsheets/d/1bdHetdGEXLgXv7A2aGvOaItKxiAuyg0Ip0UER1BjjOg/export?format=csv"
    
    try:
        # Lendo o CSV. Se houver linhas de título vazias, pode ser necessário adicionar skiprows=N
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"❌ Erro de conexão. Verifique o compartilhamento da planilha ('Qualquer pessoa com o link pode visualizar').")
        st.error(f"Detalhes do erro: {e}")
        st.stop()
        
    # --- Passo de Limpeza e Padronização de Colunas ---
    # Limpa nomes de colunas (remove espaços em branco, transforma em maiúsculas)
    df.columns = [col.strip().upper().replace(' ', '_').replace('/', '_') for col in df.columns]

    # Renomeia as colunas-chave com base no mapeamento
    df.rename(columns={k.strip().upper().replace(' ', '_').replace('/', '_'): v for k, v in COLUNA_MAP.items()}, inplace=True)

    # Converter datas
    for col in ['DATA_NOTIFICACAO', 'DATA_SINTOMAS']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

df = carregar_dados()

# Verifica se o DataFrame está vazio
if df.empty:
    st.warning("O DataFrame está vazio. Verifique se a planilha tem dados ou se há linhas de cabeçalho extras.")
    st.stop()

# st.write("### Prévia da base de dados")
# st.dataframe(df.head()) 

# ========= FILTROS NA BARRA LATERAL =========
st.sidebar.header("🔎 Filtros")

# Criando os filtros e aplicando-os
df_filtrado = df.copy()

if 'SEMANA_EPIDEMIOLOGICA' in df.columns:
    semanas = st.sidebar.multiselect("Semana Epidemiológica", sorted(df['SEMANA_EPIDEMIOLOGICA'].dropna().unique()))
    if semanas:
        df_filtrado = df_filtrado[df_filtrado['SEMANA_EPIDEMIOLOGICA'].isin(semanas)]

if 'SEXO' in df.columns:
    sexos = st.sidebar.multiselect("Sexo", df['SEXO'].dropna().unique())
    if sexos:
        df_filtrado = df_filtrado[df_filtrado['SEXO'].isin(sexos)]

if 'FAIXA_ETARIA' in df.columns:
    faixas = st.sidebar.multiselect("Faixa Etária", sorted(df['FAIXA_ETARIA'].dropna().unique()))
    if faixas:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_ETARIA'].isin(faixas)]

if 'BAIRRO' in df.columns:
    bairros = st.sidebar.multiselect("Bairro", sorted(df['BAIRRO'].dropna().unique()))
    if bairros:
        df_filtrado = df_filtrado[df_filtrado['BAIRRO'].isin(bairros)]

if 'CLASSIFICACAO_FINAL' in df.columns:
    classificacoes = st.sidebar.multiselect("Classificação Final", df['CLASSIFICACAO_FINAL'].dropna().unique())
    if classificacoes:
        df_filtrado = df_filtrado[df_filtrado['CLASSIFICACAO_FINAL'].isin(classificacoes)]

# Verifica se o DataFrame filtrado está vazio
if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()


# ========= INDICADORES PRINCIPAIS (CARDS) =========
st.header("Resumo dos Indicadores")

# FIX: Inicializa variáveis para evitar o NameError caso os blocos IF sejam ignorados
confirmados = 0 
obitos = 0
descartados = 0 

col1, col2, col3, col4 = st.columns(4)

total_notificados = len(df_filtrado)
col1.metric("Casos Notificados", total_notificados)

if 'CLASSIFICACAO_FINAL' in df_filtrado.columns:
    confirmados = (df_filtrado['CLASSIFICACAO_FINAL'].str.upper().str.strip() == "CONFIRMADO").sum()
    descartados = (df_filtrado['CLASSIFICACAO_FINAL'].str.upper().str.strip() == "DESCARTADO").sum()
    col2.metric("Confirmados", confirmados)
    col3.metric("Descartados", descartados) # Adicionado indicador de descartados

if 'EVOLUCAO' in df_filtrado.columns:
    obitos = (df_filtrado['EVOLUCAO'].str.upper().str.contains("ÓBITO", na=False)).sum()
    col3_obito = col3 if 'CLASSIFICACAO_FINAL' not in df_filtrado.columns else st.columns(4)[3] # Usa a 4a coluna se a 3a já foi usada
    col3_obito.metric("Óbitos", obitos)


# Indicador de Taxa de Letalidade (Seguro, pois 'confirmados' foi inicializado)
if confirmados > 0:
    letalidade = (obitos / confirmados) * 100
    st.columns(4)[3].metric("Taxa de Letalidade (%)", f"{letalidade:.2f}%")
else:
    st.columns(4)[3].metric("Taxa de Letalidade (%)", "N/A")


# ========= GRÁFICOS =========

# --- 1. Casos por Semana Epidemiológica ---
st.subheader("📈 Casos por Semana Epidemiológica")
if 'SEMANA_EPIDEMIOLOGICA' in df_filtrado.columns:
    df_semanal = df_filtrado.groupby("SEMANA_EPIDEMIOLOGICA").size().reset_index(name="Casos")
    fig_sem = px.line(
        df_semanal, 
        x="SEMANA_EPIDEMIOLOGICA", 
        y="Casos", 
        markers=True,
        labels={"SEMANA_EPIDEMIOLOGICA": "Semana Epidemiológica"}
    )
    st.plotly_chart(fig_sem, use_container_width=True)

# --- 2. Distribuição por Bairro (Corrigido o Plotly) ---
st.subheader("🏘️ Distribuição por Bairro")
if 'BAIRRO' in df_filtrado.columns:
    df_bairro = df_filtrado['BAIRRO'].value_counts().reset_index()
    df_bairro.columns = ['Bairro', 'Casos'] # Nomeia as colunas explicitamente
    
    fig_bairro = px.bar(
        df_bairro.head(15), # Mostra os 15 bairros com mais casos
        x='Bairro', 
        y='Casos',
        title="Top 15 Bairros por Casos Notificados"
    )
    st.plotly_chart(fig_bairro, use_container_width=True)


# --- 3. Sintomas e Comorbidades Mais Frequentes ---
st.subheader("🧩 Sintomas e Comorbidades")
sintomas_e_comorbidades = [
    "FEBRE", "MIALGIA", "CEFALEIA", "EXANTEMA", "VOMITO", "NAUSEA",
    "DOR_COSTAS", "CONJUNTVITE", "ARTRITE", "ARTRALGIA", "PETEQUIAS",
    "LEUCOPENIA", "LAÇO", "DOR_RETRO", "DIABETES", "HEMATOLOGICAS",
    "HEPATOPATIAS", "RENAL", "HIPERTENSÃO", "ACIDO_PEPT", "AUTO_IMUNE"
]

presenca_data = []
for s in sintomas_e_comorbidades:
    if s.upper() in df_filtrado.columns:
        # Conta onde a resposta é "SIM"
        count = (df_filtrado[s.upper()].astype(str).str.upper().str.strip() == "SIM").sum()
        if count > 0:
            presenca_data.append({"Item": s, "Casos": count})

if presenca_data:
    df_presenca = pd.DataFrame(presenca_data)
    
    fig_sintomas = px.bar(
        df_presenca.sort_values(by="Casos", ascending=True), 
        y="Item", 
        x="Casos", 
        orientation='h',
        title="Frequência de Manifestações/Comorbidades (Resposta 'Sim')"
    )
    st.plotly_chart(fig_sintomas, use_container_width=True)
else:
    st.info("Nenhuma manifestação ou comorbidade 'SIM' encontrada no período filtrado.")


# --- 4. Distribuição por Sexo e Faixa Etária ---
st.subheader("👥 Perfil Demográfico")
if 'SEXO' in df_filtrado.columns and 'FAIXA_ETARIA' in df_filtrado.columns:
    fig_demog = px.histogram(
        df_filtrado, 
        x="FAIXA_ETARIA", 
        color="SEXO", 
        barmode="group",
        title="Casos por Faixa Etária e Sexo"
    )
    st.plotly_chart(fig_demog, use_container_width=True)


# ========= DOWNLOAD DOS DADOS FILTRADOS =========
st.download_button(
    "📥 Baixar dados filtrados (CSV)",
    data=df_filtrado.to_csv(index=False).encode("utf-8"),
    file_name="dados_filtrados_epidemiologia.csv",
    mime="text/csv"
)

st.caption("Desenvolvido para Vigilância em Saúde.")
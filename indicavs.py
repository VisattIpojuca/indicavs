import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ========== CONFIGURAÇÃO GERAL ==========
st.set_page_config(page_title="📊 Dashboard Epidemiológico", layout="wide")

st.title("📊 Dashboard Epidemiológico Interativo")
st.caption("Fonte: Google Sheets - Atualização automática")

# Dicionário para padronizar nomes de colunas (se necessário após a limpeza)
COLUNA_MAP = {
    'SEMANA EPIDEMIOLÓGICA 2': 'SEMANA_EPIDEMIOLOGICA',
    'DATA DE NOTIFICAÇÃO': 'DATA_NOTIFICACAO',
    'DATA PRIMEIRO SINTOMAS': 'DATA_SINTOMAS',
    'FA': 'FAIXA_ETARIA',
    'BAIRRO RESIDÊNCIA': 'BAIRRO',
    'EVOLUÇÃO DO CASO': 'EVOLUCAO',
    'CLASSIFCAÇÃO': 'CLASSIFICACAO_FINAL'
}

# ========= FUNÇÃO DE CARREGAR DADOS =========
@st.cache_data
def carregar_dados():
    # URL de EXPORTAÇÃO (correta) da sua planilha
    url = "https://docs.google.com/spreadsheets/d/1bdHetdGEXLgXv7A2aGvOaItKxiAuyg0Ip0UER1BjjOg/export?format=csv"
    
    # Tentativa de leitura: o 'header=None' pode ser necessário se houver mais de uma linha de cabeçalho
    # Se a primeira linha contiver os nomes corretos, remova o 'header=None' e o 'df.columns = df.iloc[0]' abaixo.
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Erro ao carregar dados. Verifique o link de compartilhamento. Detalhes: {e}")
        st.stop()
        
    # --- Passo de Limpeza e Padronização de Colunas ---
    # Limpa nomes de colunas (remove espaços em branco, acentos, etc.)
    # Isso é essencial para evitar o erro "coluna não encontrada"
    df.columns = [col.strip().upper().replace(' ', '_') for col in df.columns]

    # Renomeia as colunas-chave
    df.rename(columns={k.strip().upper().replace(' ', '_'): v for k, v in COLUNA_MAP.items()}, inplace=True)

    # Converter datas
    for col in ['DATA_NOTIFICACAO', 'DATA_SINTOMAS']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

df = carregar_dados()

# Verifica se o DataFrame está vazio após o carregamento
if df.empty:
    st.warning("O DataFrame está vazio após o carregamento ou filtros aplicados. Verifique a fonte de dados.")
    st.stop()

# st.write("### Prévia da base de dados")
# st.dataframe(df.head()) # Linha para debug/conferência

# ========= FILTROS NA BARRA LATERAL =========
st.sidebar.header("🔎 Filtros")

# Listas de filtros possíveis (usando os nomes padronizados)
filtros = {}
if 'SEMANA_EPIDEMIOLOGICA' in df.columns:
    filtros['SEMANA_EPIDEMIOLOGICA'] = st.sidebar.multiselect(
        "Semana Epidemiológica", sorted(df['SEMANA_EPIDEMIOLOGICA'].dropna().unique())
    )
if 'SEXO' in df.columns:
    filtros['SEXO'] = st.sidebar.multiselect(
        "Sexo", df['SEXO'].dropna().unique()
    )
if 'FAIXA_ETARIA' in df.columns:
    filtros['FAIXA_ETARIA'] = st.sidebar.multiselect(
        "Faixa Etária", sorted(df['FAIXA_ETARIA'].dropna().unique())
    )
if 'BAIRRO' in df.columns:
    filtros['BAIRRO'] = st.sidebar.multiselect(
        "Bairro", sorted(df['BAIRRO'].dropna().unique())
    )
if 'ZONA' in df.columns:
    filtros['ZONA'] = st.sidebar.multiselect(
        "Zona (Urbana/Rural)", df['ZONA'].dropna().unique()
    )
if 'CLASSIFICACAO_FINAL' in df.columns:
    filtros['CLASSIFICACAO_FINAL'] = st.sidebar.multiselect(
        "Classificação Final", df['CLASSIFICACAO_FINAL'].dropna().unique()
    )

# Aplica os filtros
df_filtrado = df.copy()
for col, values in filtros.items():
    if values:
        df_filtrado = df_filtrado[df_filtrado[col].isin(values)]

# Verifica se o DataFrame filtrado está vazio
if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()


# ========= INDICADORES PRINCIPAIS (CARDS) =========
st.header("Resumo dos Indicadores")
col1, col2, col3, col4 = st.columns(4)

total_notificados = len(df_filtrado)
col1.metric("Casos Notificados", total_notificados)

if 'CLASSIFICACAO_FINAL' in df_filtrado.columns:
    confirmados = (df_filtrado['CLASSIFICACAO_FINAL'].str.upper().str.strip() == "CONFIRMADO").sum()
    descartados = (df_filtrado['CLASSIFICACAO_FINAL'].str.upper().str.strip() == "DESCARTADO").sum()
    col2.metric("Confirmados", confirmados)

if 'EVOLUCAO' in df_filtrado.columns:
    obitos = (df_filtrado['EVOLUCAO'].str.upper().str.contains("ÓBITO", na=False)).sum()
    col3.metric("Óbitos", obitos)

# Indicador de Taxa de Letalidade
if confirmados > 0:
    letalidade = (obitos / confirmados) * 100
    col4.metric("Taxa de Letalidade (%)", f"{letalidade:.2f}%")
else:
    col4.metric("Taxa de Letalidade (%)", "N/A")

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

# --- 2. Distribuição por Bairro (Corrigido) ---
st.subheader("🏘️ Distribuição por Bairro")
if 'BAIRRO' in df_filtrado.columns:
    # Cria um novo DataFrame com a contagem de casos por bairro
    df_bairro = df_filtrado['BAIRRO'].value_counts().reset_index()
    df_bairro.columns = ['Bairro', 'Casos'] # Renomeia as colunas

    fig_bairro = px.bar(
        df_bairro, 
        x='Bairro', 
        y='Casos',
        title="Casos por Bairro de Residência"
    )
    st.plotly_chart(fig_bairro, use_container_width=True)


# --- 3. Sintomas Mais Frequentes ---
st.subheader("🧩 Sintomas e Comorbidades")
sintomas = [
    "FEBRE", "MIALGIA", "CEFALEIA", "EXANTEMA", "VOMITO", "NAUSEA",
    "DOR_COSTAS", "CONJUNTVITE", "ARTRITE", "ARTRALGIA", "PETEQUIAS",
    "LEUCOPENIA", "LAÇO", "DOR_RETRO", "DIABETES", "HEMATOLOGICAS",
    "HEPATOPATIAS", "RENAL", "HIPERTENSÃO", "ACIDO_PEPT", "AUTO_IMUNE"
]

# Calcula a frequência dos sintomas/comorbidades
presenca_data = []
for s in sintomas:
    if s.upper() in df_filtrado.columns:
        # Conta onde a resposta é "SIM" (limpando espaços)
        count = (df_filtrado[s.upper()].astype(str).str.upper().str.strip() == "SIM").sum()
        if count > 0:
            presenca_data.append({"Item": s, "Casos": count})

if presenca_data:
    df_presenca = pd.DataFrame(presenca_data)
    
    fig_sintomas = px.bar(
        df_presenca.sort_values(by="Casos", ascending=False), 
        y="Item", 
        x="Casos", 
        orientation='h',
        title="Frequência de Sintomas e Comorbidades (Sim)"
    )
    st.plotly_chart(fig_sintomas, use_container_width=True)
else:
    st.info("Nenhum sintoma ou comorbidade 'SIM' encontrado no período filtrado.")


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
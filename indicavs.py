import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 Dashboard Epidemiológico", layout="wide")

st.title("📊 Dashboard Epidemiológico Interativo")
st.caption("Fonte: Google Sheets - Atualização automática")

# ========= CARREGAR DADOS =========
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1bdHetdGEXLgXv7A2aGvOaItKxiAuyg0Ip0UER1BjjOg/export?format=csv"
    df = pd.read_csv(url)

    # Converter datas
    for col in ["DATA DE NOTIFICAÇÃO", "DATA PRIMEIRO SINTOMAS"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

df = carregar_dados()

# ========= FILTROS =========
st.sidebar.header("🔎 Filtros")
if "SEMANA EPIDEMIOLÓGICA 2" in df.columns:
    semanas = st.sidebar.multiselect("Semana Epidemiológica", sorted(df["SEMANA EPIDEMIOLÓGICA 2"].dropna().unique()))
    if semanas:
        df = df[df["SEMANA EPIDEMIOLÓGICA 2"].isin(semanas)]

if "SEXO" in df.columns:
    sexos = st.sidebar.multiselect("Sexo", df["SEXO"].dropna().unique())
    if sexos:
        df = df[df["SEXO"].isin(sexos)]

if "FA" in df.columns:
    faixas = st.sidebar.multiselect("Faixa Etária", df["FA"].dropna().unique())
    if faixas:
        df = df[df["FA"].isin(faixas)]

if "BAIRRO RESIDÊNCIA" in df.columns:
    bairros = st.sidebar.multiselect("Bairro", df["BAIRRO RESIDÊNCIA"].dropna().unique())
    if bairros:
        df = df[df["BAIRRO RESIDÊNCIA"].isin(bairros)]

if "ZONA" in df.columns:
    zonas = st.sidebar.multiselect("Zona", df["ZONA"].dropna().unique())
    if zonas:
        df = df[df["ZONA"].isin(zonas)]

# ========= INDICADORES =========
col1, col2, col3, col4 = st.columns(4)

col1.metric("Casos Notificados", len(df))
if "CLASSIFCAÇÃO" in df.columns:
    confirmados = (df["CLASSIFCAÇÃO"] == "Confirmado").sum()
    descartados = (df["CLASSIFCAÇÃO"] == "Descartado").sum()
    col2.metric("Confirmados", confirmados)
    col3.metric("Descartados", descartados)

if "EVOLUÇÃO DO CASO" in df.columns:
    obitos = (df["EVOLUÇÃO DO CASO"].str.contains("Óbito", na=False)).sum()
    col4.metric("Óbitos", obitos)

# ========= GRÁFICOS =========
st.subheader("📈 Casos por Semana Epidemiológica")
if "SEMANA EPIDEMIOLÓGICA 2" in df.columns:
    fig = px.line(df.groupby("SEMANA EPIDEMIOLÓGICA 2").size().reset_index(name="Casos"),
                  x="SEMANA EPIDEMIOLÓGICA 2", y="Casos", markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Distribuição por Sexo e Faixa Etária")
if "SEXO" in df.columns and "FA" in df.columns:
    fig = px.histogram(df, x="FA", color="SEXO", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🏘️ Casos por Bairro")
if "BAIRRO RESIDÊNCIA" in df.columns:
    fig = px.bar(df["BAIRRO RESIDÊNCIA"].value_counts().reset_index(),
                 x="index", y="BAIRRO RESIDÊNCIA",
                 labels={"index":"Bairro", "BAIRRO RESIDÊNCIA":"Casos"})
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🧩 Sintomas mais frequentes")
sintomas = ["FEBRE","MIALGIA","CEFALEIA","EXANTEMA","VOMITO","NAUSEA",
            "DOR_COSTAS","CONJUNTVITE","ARTRITE","ARTRALGIA","PETEQUIAS",
            "LEUCOPENIA","LAÇO","DOR_RETRO"]
presenca = {s: (df[s] == "Sim").sum() for s in sintomas if s in df.columns}
fig = px.bar(x=list(presenca.keys()), y=list(presenca.values()), title="Sintomas presentes")
st.plotly_chart(fig, use_container_width=True)

st.subheader("⚕️ Comorbidades")
comorb = ["DIABETES","HEMATOLOGICAS","HEPATOPATIAS","RENAL","HIPERTENSÃO","ACIDO_PEPT","AUTO_IMUNE"]
comorb_presenca = {c: (df[c] == "Sim").sum() for c in comorb if c in df.columns}
fig = px.bar(x=list(comorb_presenca.keys()), y=list(comorb_presenca.values()), title="Comorbidades")
st.plotly_chart(fig, use_container_width=True)

# ========= DOWNLOAD =========
st.download_button(
    "📥 Baixar dados filtrados",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="dados_filtrados.csv",
    mime="text/csv"
)
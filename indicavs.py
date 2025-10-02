import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ========== CONFIGURAÇÃO GERAL ==========
st.set_page_config(page_title="📊 Dashboard Epidemiológico", layout="wide")

st.title("📊 Dashboard Epidemiológico Interativo")
st.caption("Fonte: Google Sheets - Atualização automática")

# Dicionário para padronizar nomes de colunas
COLUNA_MAP = {
    'SEMANA EPIDEMIOLÓGICA 2': 'SEMANA_EPIDEMIOLOGICA',
    'DATA DE NOTIFICAÇÃO': 'DATA_NOTIFICACAO',
    'DATA PRIMEIRO SINTOMAS': 'DATA_SINTOMAS',
    'FA': 'FAIXA_ETARIA', # Manter o nome FA para mapear para FAIXA_ETARIA
    'BAIRRO RESIDÊNCIA': 'BAIRRO',
    'EVOLUÇÃO DO CASO': 'EVOLUCAO',
    'CLASSIFICAÇÃO': 'CLASSIFICACAO_FINAL', # CORREÇÃO APLICADA AQUI (Assumindo CLASSIFICAÇÃO é o cabeçalho da coluna AM)
    'RAÇA/COR': 'RACA_COR',
    'ESCOLARIDADE': 'ESCOLARIDADE',
    'DISTRITO': 'DISTRITO'
}

# CHAVE DE ORDENAÇÃO MANUAL PARA O NOVO PADRÃO DE FAIXA ETÁRIA
ORDEM_FAIXA_ETARIA = [
    '1 a 4 anos', 
    '5 a 9 anos', 
    '10 a 14 anos', 
    '15 a 19 anos', 
    '20 a 39 anos', # Nova faixa agrupada
    '40 a 59 anos', # Nova faixa agrupada
    '60 anos ou mais', # Novo nome
    'IGNORADO' # Mantido para dados ausentes
]

# DICIONÁRIO PARA AGRUPAR E PADRONIZAR AS FAIXAS ETÁRIAS ANTIGAS PARA AS NOVAS
# VOCÊ PODE PRECISAR AJUSTAR AS CHAVES DESTE DICIONÁRIO PARA REFLETIR EXATAMENTE O QUE ESTÁ NA SUA PLANILHA.
MAPEAMENTO_FAIXA_ETARIA = {
    '0 a 4': '1 a 4 anos',
    '1 a 4': '1 a 4 anos',
    '5 a 9': '5 a 9 anos',
    '10 a 14': '10 a 14 anos',
    '15 a 19': '15 a 19 anos',
    
    # Agrupando faixas etárias antigas nas novas faixas de 20 a 39
    '20 a 29': '20 a 39 anos',
    '30 a 39': '20 a 39 anos',
    
    # Agrupando faixas etárias antigas nas novas faixas de 40 a 59
    '40 a 49': '40 a 59 anos',
    '50 a 59': '40 a 59 anos',
    
    # Agrupando faixas etárias antigas na nova faixa de 60 ou mais
    '60 a 69': '60 anos ou mais',
    '70 a 79': '60 anos ou mais',
    '80 ou mais': '60 anos ou mais',
    'IGNORADO': 'IGNORADO',
    # Adicione aqui outras variações que você tenha na planilha:
    # 'INDEFINIDO': 'IGNORADO',
}


# ========= FUNÇÃO DE CARREGAR DADOS =========
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1bdHetdGEXLgXv7A2aGvOaItKxiAuyg0Ip0UER1BjjOg/export?format=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"❌ Erro de conexão. Verifique o compartilhamento da planilha.")
        st.stop()
        
    # --- Passo de Limpeza e Padronização de Colunas ---
    df.columns = [col.strip().upper().replace(' ', '_').replace('/', '_') for col in df.columns]
    df.rename(columns={k.strip().upper().replace(' ', '_').replace('/', '_'): v for k, v in COLUNA_MAP.items()}, inplace=True)

    # --- NOVO PASSO: PADRONIZAÇÃO E AGRUPAMENTO DA FAIXA ETÁRIA ---
    if 'FAIXA_ETARIA' in df.columns:
        # 1. Converte a coluna para string e retira espaços (preparação para o mapeamento)
        df['FAIXA_ETARIA'] = df['FAIXA_ETARIA'].astype(str).str.strip()
        
        # 2. Aplica o mapeamento para as novas faixas e agrupa
        df['FAIXA_ETARIA'] = df['FAIXA_ETARIA'].replace(MAPEAMENTO_FAIXA_ETARIA)
        
        # 3. Substitui valores NaT/vazios restantes por 'IGNORADO'
        df['FAIXA_ETARIA'] = df['FAIXA_ETARIA'].fillna('IGNORADO')
        

    # Converter datas
    for col in ['DATA_NOTIFICACAO', 'DATA_SINTOMAS']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

df = carregar_dados()

if df.empty:
    st.warning("O DataFrame está vazio.")
    st.stop()


# ========= FILTROS NA BARRA LATERAL (FAIXA ETÁRIA ORDENADA) =========
st.sidebar.header("🔎 Filtros")

df_filtrado = df.copy() 

# --- Filtros Categóricos ---

if 'SEMANA_EPIDEMIOLOGICA' in df_filtrado.columns:
    semanas = st.sidebar.multiselect("Semana Epidemiológica", sorted(df['SEMANA_EPIDEMIOLOGICA'].dropna().unique()))
    if semanas:
        df_filtrado = df_filtrado[df_filtrado['SEMANA_EPIDEMIOLOGICA'].isin(semanas)]

if 'SEXO' in df_filtrado.columns:
    sexos = st.sidebar.multiselect("Sexo", df['SEXO'].dropna().unique())
    if sexos:
        df_filtrado = df_filtrado[df_filtrado['SEXO'].isin(sexos)]

# FILTRO DE FAIXA ETÁRIA (Corrigido e Ordenado)
if 'FAIXA_ETARIA' in df_filtrado.columns:
    faixas_presentes = df['FAIXA_ETARIA'].dropna().unique().tolist()
    faixas_ordenadas = [f for f in ORDEM_FAIXA_ETARIA if f in faixas_presentes]
    
    faixas = st.sidebar.multiselect("Faixa Etária", faixas_ordenadas) 
    if faixas:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_ETARIA'].isin(faixas)]

# FILTRO DE CLASSIFICAÇÃO (Deve funcionar agora, usando CLASSIFICACAO_FINAL)
if 'CLASSIFICACAO_FINAL' in df_filtrado.columns:
    classificacoes = st.sidebar.multiselect("Classificação Final", df['CLASSIFICACAO_FINAL'].dropna().unique())
    if classificacoes:
        df_filtrado = df_filtrado[df_filtrado['CLASSIFICACAO_FINAL'].isin(classificacoes)]
        
if 'EVOLUCAO' in df_filtrado.columns:
    evolucoes = st.sidebar.multiselect("Evolução do Caso", df['EVOLUCAO'].dropna().unique())
    if evolucoes:
        df_filtrado = df_filtrado[df_filtrado['EVOLUCAO'].isin(evolucoes)]

if 'ESCOLARIDADE' in df_filtrado.columns:
    escolaridades = st.sidebar.multiselect("Escolaridade", df['ESCOLARIDADE'].dropna().unique())
    if escolaridades:
        df_filtrado = df_filtrado[df_filtrado['ESCOLARIDADE'].isin(escolaridades)]

if 'BAIRRO' in df_filtrado.columns:
    bairros = st.sidebar.multiselect("Bairro", sorted(df['BAIRRO'].dropna().unique()))
    if bairros:
        df_filtrado = df_filtrado[df_filtrado['BAIRRO'].isin(bairros)]
        
# Verifica se o DataFrame filtrado está vazio
if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()


# ========= INDICADORES PRINCIPAIS (CARDS) =========
st.header("Resumo dos Indicadores")

confirmados = 0 
obitos = 0
descartados = 0 

col0, col1, col2, col3, col4 = st.columns(5) 

total_filtrado = len(df_filtrado)
col1.metric("Notificações no período", total_filtrado) 

if 'CLASSIFICACAO_FINAL' in df_filtrado.columns:
    confirmados = (df_filtrado['CLASSIFICACAO_FINAL'].str.upper().str.strip() == "CONFIRMADO").sum()
    descartados = (df_filtrado['CLASSIFICACAO_FINAL'].str.upper().str.strip() == "DESCARTADO").sum()
    col2.metric("Confirmados", confirmados)
    col3.metric("Descartados", descartados) 

if 'EVOLUCAO' in df_filtrado.columns:
    obitos = (df_filtrado['EVOLUCAO'].str.upper().str.contains("ÓBITO", na=False)).sum()

if confirmados > 0:
    letalidade = (obitos / confirmados) * 100
    col4.metric("Taxa de Letalidade (%)", f"{letalidade:.2f}% ({obitos} óbitos)")
else:
    col4.metric("Taxa de Letalidade (%)", "N/A")


# ========= GRÁFICOS =========

st.subheader("📈 Análise Temporal e Geográfica")
col_graf1, col_graf2 = st.columns(2)

# --- 1. Casos por Semana Epidemiológica ---
if 'SEMANA_EPIDEMIOLOGICA' in df_filtrado.columns:
    df_semanal = df_filtrado.groupby("SEMANA_EPIDEMIOLOGICA").size().reset_index(name="Casos")
    fig_sem = px.line(
        df_semanal, 
        x="SEMANA_EPIDEMIOLOGICA", 
        y="Casos", 
        markers=True,
        title="Casos por Semana Epidemiológica"
    )
    col_graf1.plotly_chart(fig_sem, use_container_width=True)

# --- 2. Distribuição por Distrito ---
if 'DISTRITO' in df_filtrado.columns:
    df_distrito = df_filtrado['DISTRITO'].value_counts().reset_index()
    df_distrito.columns = ['Distrito', 'Casos'] 
    
    fig_distrito = px.bar(
        df_distrito, 
        x='Distrito', 
        y='Casos',
        title="Distribuição de Casos por Distrito"
    )
    col_graf2.plotly_chart(fig_distrito, use_container_width=True)

# --- 3. Distribuição por Bairro ---
st.subheader("🏘️ Distribuição das notificações por Bairro")
if 'BAIRRO' in df_filtrado.columns:
    df_bairro = df_filtrado['BAIRRO'].value_counts().reset_index()
    df_bairro.columns = ['Bairro', 'Casos'] 
    
    fig_bairro = px.bar(
        df_bairro.head(15), 
        x='Bairro', 
        y='Casos',
        title="Top 15 Bairros por Casos Notificados"
    )
    st.plotly_chart(fig_bairro, use_container_width=True)

# --- 4. Relação Raça/Cor vs. Escolaridade ---
st.subheader("🎓 Perfil Social: Raça/Cor vs. Escolaridade")
if 'RACA_COR' in df_filtrado.columns and 'ESCOLARIDADE' in df_filtrado.columns:
    df_cruzado = df_filtrado.groupby(['RACA_COR', 'ESCOLARIDADE']).size().reset_index(name='Casos')

    fig_cruzado = px.bar(
        df_cruzado,
        x='RACA_COR',
        y='Casos',
        color='ESCOLARIDADE',
        barmode='group',
        title='Casos por Raça/Cor e Escolaridade'
    )
    st.plotly_chart(fig_cruzado, use_container_width=True)


# --- 5. Sintomas e Comorbidades Mais Frequentes ---
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
        count = (df_filtrado[s.upper()].astype(str).str.upper().str.strip() == "SIM").sum()
        if count > 0:
            nome_display = s.replace('_', ' ').capitalize()
            presenca_data.append({"Item": nome_display, "Casos": count})

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


# --- 6. Distribuição por Sexo e Faixa Etária (Ordenada) ---
st.subheader("👥 Perfil Demográfico")
if 'SEXO' in df_filtrado.columns and 'FAIXA_ETARIA' in df_filtrado.columns:
    
    faixas_presentes_no_grafico = df_filtrado['FAIXA_ETARIA'].dropna().unique().tolist()
    faixas_para_grafico = [f for f in ORDEM_FAIXA_ETARIA if f in faixas_presentes_no_grafico]

    fig_demog = px.histogram(
        df_filtrado, 
        x="FAIXA_ETARIA", 
        color="SEXO", 
        barmode="group",
        title="Casos por Faixa Etária e Sexo"
    )
    # Define a ordem do eixo X do gráfico (usando a nova ordem padronizada)
    fig_demog.update_xaxes(categoryorder='array', categoryarray=faixas_para_grafico)
    
    st.plotly_chart(fig_demog, use_container_width=True)


# ========= DOWNLOAD DOS DADOS FILTRADOS =========
st.download_button(
    "📥 Baixar dados filtrados (CSV)",
    data=df_filtrado.to_csv(index=False).encode("utf-8"),
    file_name="dados_filtrados_epidemiologia.csv",
    mime="text/csv"
)

st.caption("Desenvolvido para Vigilância em Saúde.")
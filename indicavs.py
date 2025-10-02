import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import unicodedata # Módulo essencial para lidar com acentos/caracteres ocultos

# ========== CONFIGURAÇÃO GERAL ==========
st.set_page_config(page_title="🦟 Dengue Ipojuca", layout="wide")

st.title("🦟 Dashboard Vigilância das Arboviroses (Dengue)")
st.caption("Fonte: Grência de Promoção, Prevenção e Vigilância Epidemiológica 📊🗺️")

# Dicionário FINAL para padronizar nomes de colunas no DataFrame LIMPO.
FINAL_RENAME_MAP = {
    'SEMANA_EPIDEMIOLOGICA': 'SEMANA_EPIDEMIOLOGICA',
    'SEMANA_EPIDEMIOLOGICA_2': 'SEMANA_EPIDEMIOLOGICA',
    'DATA_NOTIFICACAO': 'DATA_NOTIFICACAO',
    'DATA_DE_NOTIFICACAO': 'DATA_NOTIFICACAO',
    'DATA_PRIMEIRO_SINTOMAS': 'DATA_SINTOMAS',
    'DATA_PRIMEIROS_SINTOMAS': 'DATA_SINTOMAS',
    'FA': 'FAIXA_ETARIA', 
    'BAIRRO_RESIDENCIA': 'BAIRRO',
    'EVOLUCAO_DO_CASO': 'EVOLUCAO',
    'CLASSIFICACAO': 'CLASSIFICACAO_FINAL',
    'RACA_COR': 'RACA_COR',
    'ESCOLARIDADE': 'ESCOLARIDADE',
    'DISTRITO': 'DISTRITO'
}

# CHAVE DE ORDENAÇÃO MANUAL PARA O NOVO PADRÃO DE FAIXA ETÁRIA
ORDEM_FAIXA_ETARIA = [
    '1 a 4 anos', '5 a 9 anos', '10 a 14 anos', '15 a 19 anos', 
    '20 a 39 anos', '40 a 59 anos', '60 anos ou mais', 'IGNORADO'
]

# DICIONÁRIO PARA AGRUPAR E PADRONIZAR AS FAIXAS ETÁRIAS ANTIGAS PARA AS NOVAS
MAPEAMENTO_FAIXA_ETARIA = {
    '0 a 4': '1 a 4 anos', '1 a 4': '1 a 4 anos', '5 a 9': '5 a 9 anos', 
    '10 a 14': '10 a 14 anos', '15 a 19': '15 a 19 anos',
    '20 a 29': '20 a 39 anos', '30 a 39': '20 a 39 anos',
    '40 a 49': '40 a 59 anos', '50 a 59': '40 a 59 anos',
    '60 a 69': '60 anos ou mais', '70 a 79': '60 anos ou mais', 
    '80 ou mais': '60 anos ou mais', 'IGNORADO': 'IGNORADO',
}

# FUNÇÃO DE LIMPEZA DE COLUNAS: CORREÇÃO DEFINITIVA COM UNICODE NORMALIZATION
def limpar_nome_coluna(col):
    col_normalized = unicodedata.normalize('NFKD', col).encode('ascii', 'ignore').decode('utf-8')
    col_limpa = col_normalized.strip().upper().replace(' ', '_').replace('/', '_').replace('-', '_')
    return col_limpa


# ========= FUNÇÃO DE CARREGAR DADOS (FLUXO ROBUSTO) =========
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1bdHetdGEXLgXv7A2aGvOaItKxiAuyg0Ip0UER1BjjOg/export?format=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"❌ Erro de conexão. Verifique o compartilhamento da planilha.")
        st.stop()
        
    
    # --- Passo 1: Limpeza Universal de Nomes de Colunas ---
    df.columns = [limpar_nome_coluna(col) for col in df.columns] 

    # --- Passo 2: Padronização Final de Nomes ---
    rename_dict = {}
    for k_limpo, v_final in FINAL_RENAME_MAP.items():
        if k_limpo in df.columns:
            rename_dict[k_limpo] = v_final
            
    df.rename(columns=rename_dict, inplace=True)
    
    # --- Passo 3: Limpeza de Colunas Duplicadas ---
    df = df.loc[:,~df.columns.duplicated()].copy()


    # --- PADRONIZAÇÃO E AGRUPAMENTO DA FAIXA ETÁRIA ---
    if 'FAIXA_ETARIA' in df.columns:
        df['FAIXA_ETARIA'] = df['FAIXA_ETARIA'].astype(str).str.strip()
        df['FAIXA_ETARIA'] = df['FAIXA_ETARIA'].replace(MAPEAMENTO_FAIXA_ETARIA)
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

# FILTRO CLASSIFICAÇÃO FINAL (NO TOPO)
if 'CLASSIFICACAO_FINAL' in df_filtrado.columns:
    classificacoes = st.sidebar.multiselect("Classificação Final", df['CLASSIFICACAO_FINAL'].dropna().unique())
    if classificacoes:
        df_filtrado = df_filtrado[df_filtrado['CLASSIFICACAO_FINAL'].isin(classificacoes)]
        
# FILTRO DE SEMANA EPIDEMIOLÓGICA (AGORA ESTÁVEL)
if 'SEMANA_EPIDEMIOLOGICA' in df_filtrado.columns: 
    semanas = st.sidebar.multiselect("Semana Epidemiológica", sorted(df['SEMANA_EPIDEMIOLOGICA'].dropna().unique()))
    if semanas:
        df_filtrado = df_filtrado[df_filtrado['SEMANA_EPIDEMIOLOGICA'].isin(semanas)]
else:
    st.sidebar.warning("Coluna 'Semana Epidemiológica' não encontrada. Verifique o nome na planilha.")


if 'SEXO' in df_filtrado.columns:
    sexos = st.sidebar.multiselect("Sexo", df['SEXO'].dropna().unique())
    if sexos:
        df_filtrado = df_filtrado[df_filtrado['SEXO'].isin(sexos)]

# Ordenação da Faixa Etária
if 'FAIXA_ETARIA' in df_filtrado.columns:
    faixas_presentes = df['FAIXA_ETARIA'].dropna().unique().tolist()
    faixas_ordenadas = [f for f in ORDEM_FAIXA_ETARIA if f in faixas_presentes]
    faixas = st.sidebar.multiselect("Faixa Etária", faixas_ordenadas) 
    if faixas:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_ETARIA'].isin(faixas)]

# FILTRO DE EVOLUÇÃO DO CASO 
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


# ========= INDICADORES PRINCIPAIS (CARDS) - TRECHO ALTERADO PARA ALINHAMENTO E LÓGICA =========
st.header("Resumo dos Indicadores")

confirmados = 0 
obitos = 0
descartados = 0 

# ALTERAÇÃO: Reduzido para 4 colunas (col0 a col3) para remover o espaço vazio inicial
col0, col1, col2, col3 = st.columns(4) 

total_filtrado = len(df_filtrado)
# ALTERAÇÃO: Métrica movida para a primeira coluna (col0)
col0.metric("Notificações no período", total_filtrado) 

if 'CLASSIFICACAO_FINAL' in df_filtrado.columns:
    
    CLASSIFICACOES_CONFIRMADO = ["DENGUE", "DENGUE COM SINAIS DE ALARME"]
    classificacao_upper = df_filtrado['CLASSIFICACAO_FINAL'].astype(str).str.upper().str.strip()
    
    confirmados = classificacao_upper.isin(CLASSIFICACOES_CONFIRMADO).sum()
    descartados = (classificacao_upper == "DESCARTADO").sum()
    
    # Métricas movidas para col1 e col2
    col1.metric("Confirmados", confirmados)
    col2.metric("Descartados", descartados) 

if 'EVOLUCAO' in df_filtrado.columns:
    obitos = (df_filtrado['EVOLUCAO'].astype(str).str.upper().str.contains("ÓBITO", na=False)).sum()

if confirmados > 0:
    letalidade = (obitos / confirmados) * 100
    # Métrica movida para col3
    col3.metric("Taxa de Letalidade (%)", f"{letalidade:.2f}% ({obitos} óbitos)")
else:
    col3.metric("Taxa de Letalidade (%)", "N/A")


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
st.subheader("🎓 Perfil Social: Raça/Cor e Escolaridade")
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
st.subheader("🩺 Sintomas e Comorbidades")
sintomas_e_comorbidades = [
    "FEBRE", "MIALGIA", "CEFALEIA", "EXANTEMA", "VOMITO", "NAUSEA",
    "DOR_COSTAS", "CONJUNTVITE", "ARTRITE", "ARTRALGIA", "PETEQUIAS",
    "LEUCOPENIA", "LAÇO", "DOR_RETRO", "DIABETES", "HEMATOLOGICAS",
    "HEPATOPATIAS", "RENAL", "HIPERTENSÃO", "ACIDO_PEPT", "AUTO_IMUNE"
]

presenca_data = []
for s in sintomas_e_comorbidades:
    s_limpa = limpar_nome_coluna(s)
    
    # Busca a coluna pelo nome limpo gerado pelo processo de limpeza geral
    if s_limpa in df_filtrado.columns:
        count = (df_filtrado[s_limpa].astype(str).str.upper().str.strip() == "SIM").sum()
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

st.caption("Desenvolvido pelo Cievs Ipojuca.")
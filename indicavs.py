# Mantenha o COLUNA_MAP e demais variáveis como estão.
# Substitua APENAS a função carregar_dados()

# ========= FUNÇÃO DE CARREGAR DADOS COM DIAGNÓSTICO =========
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1bdHetdGEXLgXv7A2aGvOaItKxiAuyg0Ip0UER1BjjOg/export?format=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"❌ Erro de conexão. Verifique o compartilhamento da planilha.")
        st.stop()

    # >>>>> DIAGNÓSTICO: MOSTRA AS COLUNAS ORIGINAIS <<<<<
    # Isso mostrará os nomes EXATOS das colunas lidas.
    st.warning(f"COLUNAS LIDOS DO CSV (USE ESTES NOMES NO MAPA, SE NECESSÁRIO):\n{df.columns.tolist()}")

    # --- Passo de Limpeza e Padronização de Colunas ---
    # 1. Aplica a limpeza robusta em TODAS as colunas do DataFrame
    df.columns = [limpar_nome_coluna(col) for col in df.columns]

    # 2. Cria o dicionário de renomeação
    rename_dict = {}
    cleaned_df_columns = df.columns.tolist()

    for k_original, v_final in COLUNA_MAP.items():
        k_limpa = limpar_nome_coluna(k_original)
        
        if k_limpa in cleaned_df_columns:
            rename_dict[k_limpa] = v_final

    df.rename(columns=rename_dict, inplace=True)
    
    # 3. CORREÇÃO DE CONTINGÊNCIA SUPER ROBUSTA PARA SEMANA_EPIDEMIOLOGICA
    if 'SEMANA_EPIDEMIOLOGICA' not in df.columns:
        for col in df.columns:
            if 'SEMANA' in col and 'EPIDEMIOLOGICA' in col:
                df.rename(columns={col: 'SEMANA_EPIDEMIOLOGICA'}, inplace=True)
                break

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
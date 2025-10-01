# 📊 Dashboard Epidemiológico Interativo

Este painel foi desenvolvido em **Streamlit** para monitoramento de dados epidemiológicos a partir de uma planilha no **Google Sheets**.  
Ele atualiza automaticamente sempre que a tabela recebe novas linhas, permitindo análises em tempo real.

---

## 🔍 Funcionalidades

- **Filtros dinâmicos** por:
  - Semana Epidemiológica
  - Data de Notificação
  - Sexo
  - Faixa Etária
  - Gestante
  - Raça/Cor
  - Escolaridade
  - Bairro de Residência
  - Distrito
  - Zona (Urbana/Rural)
  - Classificação Final
  - Evolução do Caso

- **Indicadores principais**:
  - Total de casos notificados
  - Casos confirmados e descartados
  - Casos por sexo
  - Casos por faixa etária
  - Casos em gestantes
  - Taxa de letalidade
  - Distribuição por zona (urbana/rural)

- **Visualizações interativas**:
  - Linha do tempo por semana epidemiológica
  - Distribuição por sexo e faixa etária
  - Casos por bairro/distrito
  - Sintomas mais frequentes
  - Comorbidades relatadas
  - Evolução dos casos (cura, óbito, etc.)

- **Exportação de dados**:
  - Download em CSV/Excel dos dados filtrados
  - Exportação de gráficos interativos (Plotly)

---

## 🚀 Como Executar

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-repositorio/dashboard-epidemiologico.git
   cd dashboard-epidemiologico
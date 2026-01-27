1. 📄 Atualize o requirements.txt
Substitua o conteúdo atual por este (está completo e organizado):

Plaintext
streamlit
pandas
numpy
plotly
requests
python-dotenv
lxml
openpyxl
pyarrow
beautifulsoup4
google-generativeai
2. 📝 Crie/Atualize o README.md
Esse é o texto que vai aparecer na página inicial do GitHub. Fiz um modelo profissional destacando as tecnologias e as funcionalidades "Sênior" (Duration, VaR, Integração API).

Markdown
# 🏛️ Tesouro Quant v1.0

**Tesouro Quant** é uma plataforma de inteligência financeira e precificação de títulos públicos brasileiros (Tesouro Direto). 

O sistema coleta dados em tempo real, calcula riscos de mercado (Duration, Convexidade, VaR) e utiliza Inteligência Artificial para consultoria de investimentos.

![Status](https://img.shields.io/badge/Status-Stable-green) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-red)

## 🚀 Funcionalidades

### 📊 1. Simulador de Renda Fixa (Real-Time)
- **Scraping de Taxas:** Monitoramento em tempo real das taxas do Tesouro (Prefixado, IPCA+, Selic, Renda+, Educa+).
- **Cálculo Preciso:** Projeção líquida descontando Imposto de Renda (tabela regressiva) e Taxa de Custódia B3.
- **Comparativo:** Benchmarking automático contra Poupança e CDI.

### 🛡️ 2. Gestão de Risco Profissional
- **Mark-to-Market:** Cálculo de *Duration* (Macaulay & Modified) para medir sensibilidade a juros.
- **VaR (Value at Risk):** Estimação de perda máxima provável em cenários de estresse.
- **Teste de Estresse:** Simulação de choques na curva de juros (+1%, -1%) e impacto no patrimônio.

### 🌐 3. Dados Macro (Banco Central)
- Integração automática com APIs do **Banco Central do Brasil (SGS e Olinda)**.
- **Taxa Selic Meta:** Atualização automática via API SGS.
- **Boletim Focus:** Coleta automática das expectativas de inflação (IPCA) do mercado para 2026/2027.

### 🤖 4. Consultor U AI (Gemini Flash)
- Chatbot financeiro integrado com a API **Google Gemini 1.5 Flash**.
- Responde dúvidas sobre economia, estratégia de aportes e explica termos técnicos.

---

## 🛠️ Instalação e Execução

### Pré-requisitos
- Python 3.10 ou superior.

### 1. Clone o repositório
```bash
git clone [https://github.com/SEU-USUARIO/tesouro-quant.git](https://github.com/SEU-USUARIO/tesouro-quant.git)
cd tesouro-quant
2. Instale as dependências
Bash
pip install -r requirements.txt
3. (Opcional) Configure a API Key do Google
Se quiser usar o Chatbot (Consultor U AI), crie um arquivo .env na raiz ou configure no .streamlit/secrets.toml:

Ini, TOML
GOOGLE_API_KEY = "sua_chave_aqui"
4. Execute o Sistema
Bash
streamlit run src/app/streamlit_app.py
📂 Estrutura do Projeto
Plaintext
tesouro-quant/
├── data/                  # Armazenamento de dados (Parquet)
├── scripts/               # Robôs de coleta (ETL)
│   ├── run_fetch.py       # Scraper de Títulos
│   ├── run_fetch_selic.py # API Selic
│   └── run_fetch_inflation.py # API Focus
├── src/
│   ├── app/               # Interface (Streamlit)
│   │   ├── streamlit_app.py  # Home
│   │   └── pages/            # Simulador, Carteira, Macro
│   └── core/              # Motor de Cálculo (Duration, Pricing)
└── requirements.txt       # Dependências
⚠️ Disclaimer
Este projeto tem fins educacionais e informativos. Não constitui recomendação de investimento.

Desenvolvido com 💙 por [Seu Nome]


### 🚀 O Grand Finale

Depois de salvar esses dois arquivos, é só rodar o combo final no terminal:

```bash
git add requirements.txt README.md
git commit -m "Docs: Atualiza Readme e dependências para v1.0"
git push
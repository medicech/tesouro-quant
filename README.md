# 🏛️ Tesouro Quant v1.0

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-red)
![Status](https://img.shields.io/badge/Status-Active-success)

**Tesouro Quant** é uma plataforma de inteligência financeira e precificação de títulos públicos brasileiros (Tesouro Direto). O sistema coleta dados em tempo real, calcula métricas avançadas de risco de mercado (Duration, Convexidade, VaR) e utiliza Inteligência Artificial Generativa para consultoria de investimentos.

---

## 🚀 Funcionalidades

### 📊 1. Simulador de Renda Fixa (Real-Time)
* **Scraping de Taxas:** Monitoramento em tempo real das taxas do Tesouro (Prefixado, IPCA+, Selic, Renda+, Educa+) via *Investidor10*.
* **Cálculo Preciso:** Projeção de rentabilidade líquida descontando automaticamente:
    * Imposto de Renda (Tabela Regressiva).
    * Taxa de Custódia da B3 (0.20% a.a.).
* **Comparativo:** Benchmarking automático contra Poupança e CDI.

### 🛡️ 2. Gestão de Risco Profissional
* **Mark-to-Market:** Precificação a mercado dos títulos.
* **Duration:** Cálculo de *Macaulay Duration* e *Modified Duration* para medir a sensibilidade do portfólio às variações na taxa de juros.
* **VaR (Value at Risk):** Estimação estatística da perda máxima provável em cenários normais de mercado.
* **Teste de Estresse:** Simulação de choques na curva de juros (+1%, -1%) e impacto imediato no patrimônio.

### 🌐 3. Dados Macro (Banco Central)
* **Integração API Oficial:** Conexão automática com as APIs do Banco Central do Brasil (SGS e Olinda).
* **Curva de Juros:** Construção da ETTJ (Estrutura a Termo da Taxa de Juros) Nominal e Real.
* **Boletim Focus:** Coleta e visualização das expectativas de mercado (IPCA e Selic) para os próximos anos.

### 🤖 4. Consultor U AI (Gemini)
* **AI Integrada:** Chatbot financeiro alimentado pelo modelo **Google Gemini 1.5 Flash**.
* **Consultoria:** Responde dúvidas sobre economia, explica termos técnicos e analisa estratégias de aportes com base no contexto do usuário.

---

## 🛠️ Instalação e Execução

### Pré-requisitos
* Python 3.10 ou superior.
* Conta no Google AI Studio (para a chave da API do Gemini).

### 1. Clone o repositório
```bash
git clone [https://github.com/SEU-USUARIO/tesouro-quant.git](https://github.com/SEU-USUARIO/tesouro-quant.git)
cd tesouro-quant

2. Instale as dependências
Bash
pip install -r requirements.txt

3. Configuração de API (Opcional)
Para utilizar o Consultor U AI, configure sua chave do Google Gemini. Crie um arquivo .streamlit/secrets.toml ou um arquivo .env:

Ini, TOML
# .streamlit/secrets.toml
GOOGLE_API_KEY = "sua_chave_aqui"

4. Execute o Sistema
Bash
streamlit run src/app/streamlit_app.py

📂 Estrutura do Projeto
Plaintext
tesouro-quant/
├── data/                  # Armazenamento de dados processados (Parquet)
│   └── processed/         # Arquivos de catálogo e séries históricas
├── scripts/               # Robôs de coleta de dados (ETL)
│   ├── run_fetch.py       # Scraper de Títulos (Investidor10)
│   ├── run_fetch_selic.py # API Selic (Banco Central SGS)
│   └── run_fetch_inflation.py # API Focus (Banco Central Olinda)
├── src/
│   ├── app/               # Interface do Usuário (Streamlit)
│   │   ├── streamlit_app.py  # Página Inicial (Dashboard)
│   │   └── pages/            # Módulos: Simulador, Carteira, Macro, Consultor
│   └── core/              # Motor de Cálculo Financeiro
│       ├── calc.py        # Matemática Financeira
│       └── risk.py        # Cálculos de Duration e VaR
└── requirements.txt       # Lista de dependências
⚠️ Disclaimer
Este projeto tem fins estritamente educacionais e informativos. As simulações e dados apresentados não constituem recomendação de compra ou venda de ativos mobiliários. Rentabilidade passada não representa garantia de rentabilidade futura.



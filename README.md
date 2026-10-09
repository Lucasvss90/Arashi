# 🌪️ Arashi - Sistema Integrado de Gestão Industrial e PCP

O **Arashi** é uma plataforma web completa para gestão da produção, estoque, engenharia de produtos (BOM), compras, custos e monitoramento industrial (Andon / OEE) voltada à manufatura e manufatura aditiva (impressão 3D).

---

## 🚀 Funcionalidades Principais

- **📦 Engenharia & Estrutura de Produtos (BOM):**
  - Cadastro de matérias-primas e insumos (filamentos, componentes, resinas).
  - Estruturação de Lista de Materiais (BOM) com cálculo automático de custos diretos.
  - Parâmetros de precificação, markup e margem de contribuição.

- **🏭 PCP & Ordens de Produção (OP):**
  - Geração e controle de ordens de fabricação.
  - Rastreabilidade de lotes, apontamento de tempo e status produtivo.

- **📊 Monitoramento & Andon em Tempo Real:**
  - Painel de status de máquinas e linhas operacionais.
  - Alertas visuais e indicadores de desempenho (OEE / Disponibilidade).

- **🛒 Gestão de Compras & Suprimentos:**
  - Acompanhamento de pedidos de compra em trânsito e previsão de entrega.
  - Histórico de observações e justificativas de prazos.

- **💰 Análise de Custos & Rentabilidade:**
  - Demonstrativo de custos unitários e despesas fixas fabris.
  - Integração direta entre engenharia de produtos e compras.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Login, Bcrypt
- **Banco de Dados:** SQLite (com suporte a migrações em tempo de inicialização)
- **Frontend:** HTML5, CSS3 moderno com tema escuro (Dark Glassmorphism), JavaScript modular
- **Deploy & Contêiner:** Docker, Docker Compose, Gunicorn

---

## ⚙️ Instalação e Execução Local

### Pré-requisitos
- Python 3.11 ou superior instalado
- Git

### 1. Clonar o Repositório
```bash
git clone https://github.com/Lucasvss90/Arashi.git
cd Arashi
```

### 2. Criar e Ativar Ambiente Virtual
```bash
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / Mac:
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a Aplicação
```bash
python run.py
```
Acesse no seu navegador: `http://localhost:5000`

---

## 🐳 Execução via Docker

Para rodar via contêiner com persistência de dados:

```bash
docker-compose up --build -d
```

---

## 📂 Estrutura do Projeto

```
Arashi/
├── app/
│   ├── static/          # Arquivos CSS, JS e imagens
│   ├── templates/       # Templates Jinja2 (HTML)
│   ├── __init__.py      # Inicialização do App Factory
│   ├── models.py        # Modelos SQLAlchemy do banco de dados
│   └── routes.py        # Rotas e controladores da aplicação
├── instance/            # Armazenamento do banco de dados SQLite local
├── seed_*.py            # Scripts de carga inicial de dados e testes
├── test_*.py            # Testes unitários e de integração
├── Dockerfile           # Imagem Docker da aplicação
├── docker-compose.yml   # Orquestração do contêiner Docker
├── requirements.txt     # Dependências Python
├── run.py               # Ponto de entrada da aplicação
└── README.md            # Documentação do projeto
```

---

## 👤 Autor

Desenvolvido por **Lucas Vinicius Santos Silva** ([@Lucasvss90](https://github.com/Lucasvss90)).

📚 API Pública para Consulta de Livros
Uma API desenvolvida para extração, transformação e disponibilização de dados de livros via API pública. Incluindo funcionalidades de autenticação, estatísticas e predições utilizando modelos de machine learning.


📌 Funcionalidades
- Listagem, busca e estatísticas de livros.
- Autenticação via token JWT.
- Previsão de preço de livros com base em data de compra e taxa de câmbio.
- Geração de dados de treino/teste para ML.


📐 Arquitetura do Projeto
O projeto é estruturado em módulos bem definidos:

TECH_CHALLENGE_BOOKS/
├── API/                    # Módulo principal da API (FastAPI)
│   ├── main.py             # Ponto de entrada da aplicação
│   ├── routes.py           # Rotas principais
│   ├── ml_routes.py        # Rotas relacionadas ao ML
│   ├── auth.py             # Rotas de autenticação
│   └── requirements.txt    # Dependências do projeto
│
├── data_base/              # Arquivos e bancos de dados locais
│   ├── *.csv, *.db         # Dados de entrada e saída
│
├── extract/                # Notebooks e scripts de extração
│   ├── extract_books.ipynb
│   └── extract_gbp_today.py
│
├── ml/                     # Modelos de machine learning
│   ├── data_processing.py  # Pré-processamento
│   ├── modelo_ml.ipynb     # Notebook de modelagem
│   └── modelo_gbp_blr.pkl  # Modelo treinado


📋 Pré-requisitos
- Python 3.8+
- pip


🚀 Instalação
**bash**
- Clone o projeto
git clone https://github.com/gLima46/Tech_Challenge_Books.git
cd Tech_Challenge_Books/API

- Instale as dependências
pip install -r requirements.txt


▶️ Executando a API
Dentro da pasta `API`, execute:
**bash**
uvicorn main:app --reload

Acesse no navegador:
Procure em que porta está rodando a api. Exemplo: "INFO:     Uvicorn running on http://127.0.0.1:8000".
Em seguida copie o http que ele retornou e insira na barra de pesquisa do navegador.

Para acessar o Swagger adicione /docs no final da uri, rcemplo: http://127.0.0.1:8000/docs


🔁 Documentação das Rotas da API
| Método | Rota                    | Descrição                  |
| ------ | ----------------------- | -------------------------- |
| POST   | `/api/v1/auth/register` | Cria um novo usuário       |
| POST   | `/api/v1/auth/login`    | Realiza login (seta token) |
| POST   | `/api/v1/auth/logout`   | Faz logout (remove cookie) |
| POST   | `/api/v1/auth/refresh`  | Gera um novo token         |


📚 Core (Books)
| Método | Rota                        | Descrição                                 |
| ------ | --------------------------- | ----------------------------------------- |
| GET    | `/api/v1/health`            | Verifica conectividade com banco          |
| GET    | `/api/v1/books`             | Lista todos os livros                     |
| GET    | `/api/v1/books/search`      | Busca por título e/ou categoria           |
| GET    | `/api/v1/books/top-rated`   | Livros com melhor avaliação               |
| GET    | `/api/v1/books/price-range` | Livros dentro de uma faixa de preço       |
| GET    | `/api/v1/books/{book_id}`   | Busca livro por ID                        |
| GET    | `/api/v1/categories`        | Lista todas as categorias                 |
| GET    | `/api/v1/stats/overview`    | Estatísticas gerais do acervo             |
| GET    | `/api/v1/stats/categories`  | Estatísticas por categoria                |
| POST   | `/api/v1/run-extraction`    | Executa script de scraping (requer login) |

🤖 ML
| Método | Rota                                | Descrição                                      |
| ------ | ----------------------------------- | ---------------------------------------------- |
| GET    | `/api/v1/ml/features`               | Retorna features formatadas para ML            |
| GET    | `/api/v1/ml/training-data-books`    | Gera/retorna CSV de treino de livros           |
| GET    | `/api/v1/ml/test-data-books`        | Gera/retorna CSV de teste de livros            |
| GET    | `/api/v1/ml/training-data-exchange` | Retorna dataset de treino para câmbio GBP→BRL  |
| POST   | `/api/v1/ml/predictions`            | Retorna previsão de preço em BRL para um livro |


🔧 Exemplos de Chamadas
- **Registro de Usuário**
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "admin",
  "password": "123456"
}

- **Login**
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "123456"
}

Resposta:
json
{
  "message": "Login successful"
}

- **Listar livros Livros**
GET /api/v1/books/books

Resposta:
json
[
  {
    "id": 1,
    "title": "Book Title",
    "category": "Fiction",
    ...
  }
]

- **Previsão de Preço com ML**
POST /api/v1/ml/predictions
Content-Type: application/json

{
  "book_name": "The Great Book",
  "purchase_date": "2025-10-01"
}

Resposta:
json
{
  "book_name": "The Great Book",
  "price_gbp": 25.99,
  "today_exchange_rate": 7.5,
  "current_price_brl": 194.93,
  "purchase_date": "2025-10-01",
  "predicted_exchange_rate": 7.65,
  "predicted_price_brl_on_purchase_date": 198.34
}


📦 Dados

O projeto utiliza arquivos `.csv` e `.db` armazenados em `data_base/` como fonte de dados para extração, visualização e modelagem.

🧰 Tecnologias Utilizadas

- **FastAPI** – framework web moderno para APIs
- **SQLite** – banco de dados leve para persistência local
- **Pandas & NumPy** – manipulação de dados
- **Scikit-learn** – modelagem e predição
- **Uvicorn** – servidor ASGI leve
- **JWT (JSON Web Tokens)** – autenticação segura

📈 Arquitetura
A arquitetura se encontra no arquivo chamado arquitetura.png
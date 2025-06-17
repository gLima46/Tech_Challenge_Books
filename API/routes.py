from fastapi import APIRouter, HTTPException, Query,Request, Depends
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from auth import token_required
from nbconvert.preprocessors import ExecutePreprocessor
import asyncio
import sys
import subprocess

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#para startar a api
#uvicorn main:app --reload

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(__file__), "../data_base/books.db")
db = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

@router.get("/health")
def health_check(request: Request):
    """
    Verifica o status da api e a conectividade com a base de dados.
    """
    try:
        with db.connect() as conn:
            conn.execute(text("SELECT title FROM books"))
        return {
            "status": "ok",
            "db_connection": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "db_connection": "failed", "error": str(e)})


@router.get("/books")
def list_books():
    """
    Lista todos os livros disponíveis na base de dados.
    """
    with db.connect() as conn:
            result = conn.execute(text("SELECT * FROM books")).mappings().fetchall()
            return list(result)

@router.get("/books/search")
def search_books(title: str = Query(None), category: str = Query(None)):
    """
    Lista livros por título e/ou categoria.
    """
    with db.connect() as conn:
        params = {}
        if title:
            params["title"] = f"%{title}%"
            query = "SELECT * FROM books WHERE title LIKE :title"
        if category:
            params["category"] = f"%{category}%"
            query = "SELECT * FROM books WHERE category LIKE :category"
        result = conn.execute(text(query), params).mappings().fetchall()
        return list(result)

@router.get("/books/top-rated")
def top_rated_books():
    """
    Lista os livros com melhor avaliação.
    """
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    id,
                    title,
                    CONCAT(Simbolo_Moeda, ' ', price) AS price,
                    availability,
                    rating,
                    category,
                    image_url
                FROM
                    books
                ORDER BY
                    CASE rating
                        WHEN 'One' THEN 1
                        WHEN 'Two' THEN 2
                        WHEN 'Three' THEN 3
                        WHEN 'Four' THEN 4
                        WHEN 'Five' THEN 5                   
                    END
                DESC;
            """)).mappings().fetchall()
        return list(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books/price-range")
def books_by_price_range(min: int = Query(0), max: int = Query(9999)):
    """
    Filtra livros dentro de uma faixa de preço específica.
    """
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT *
                FROM books
                WHERE price BETWEEN :min AND :max
            """), {"min": min, "max": max}).mappings().fetchall()
        return list(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books/{book_id}")
def get_book(book_id: int):
    """
    Lista um livro específico de acordo com o id dele.
    """
    with db.connect() as conn:
        result = conn.execute(text("SELECT * FROM books WHERE id = :id"), {"id": book_id}).fetchone()
        if result:
            return list(result)
        else:
            raise HTTPException(status_code=404, detail="Book not found")

@router.get("/categories")
def list_categories():
    """
    Lista todas as categorias de livros.
    """
    with db.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT category FROM books")).fetchall()
        return [row[0] for row in result if row[0]]

@router.get("/stats/overview")
def stats_overview():
    """
    Lista estatísticas gerais da coleção (total de livros, preço médio, distribuição de ratings).
    """
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) AS total_books,
                    CONCAT(Simbolo_Moeda, ' ', ROUND(AVG(price), 2)) AS avg_price,
                    SUM(CASE WHEN rating = 'One' THEN 1 ELSE 0 END) AS rating_One,
                    SUM(CASE WHEN rating = 'Two' THEN 1 ELSE 0 END) AS rating_Two,
                    SUM(CASE WHEN rating = 'Three' THEN 1 ELSE 0 END) AS rating_Three,
                    SUM(CASE WHEN rating = 'Four' THEN 1 ELSE 0 END) AS rating_Four,
                    SUM(CASE WHEN rating = 'Five' THEN 1 ELSE 0 END) AS rating_Five
                FROM books;

            """)).mappings().first()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/categories")
def stats_by_category():
    """
    Lista estatísticas detalhadas por categoria (quantidade de livros, preços por categoria). 
    """
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    category,
                    COUNT(*) AS total_books,
                    ROUND(AVG(price), 2) AS avg_price
                FROM books
                GROUP BY category
            """)).mappings().fetchall()
        return list(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/books/top-rated")
def top_rated_books():
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT id, title, author, rating
                FROM books
                ORDER BY rating DESC
            """)).mappings().fetchall()
        return list(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

ep = ExecutePreprocessor(timeout=800, kernel_name='python3')  # 15 minutos

@router.post("/run-extraction")
@token_required
def run_extraction(request: Request):
    """
    Executa o script extract_books.py e retorna o CSV gerado como download.
    """
    script_path = os.path.join(os.path.dirname(__file__), "../extract_books/extract_books.py")
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_base/books.csv"))

    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Script extract_books.py não encontrado.")

    try:
        result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=800)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erro ao executar o script: {result.stderr}")

        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Arquivo CSV não foi gerado.")

        return FileResponse(
            path=csv_path,
            filename="books.csv",
            media_type="text/csv"
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Tempo limite de execução excedido (timeout).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")


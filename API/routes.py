import os
import sys
import asyncio
import subprocess

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from nbconvert.preprocessors import ExecutePreprocessor

from auth import token_required

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

router = APIRouter(tags=["Core"])

DB_PATH = os.path.join(os.path.dirname(__file__), "../data_base/books.db")
DB_PATH_FEATURES = os.path.join(os.path.dirname(__file__), "../data_base/features_books.db")

db = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
db_features = create_engine(f"sqlite:///{DB_PATH_FEATURES}", connect_args={"check_same_thread": False})


@router.get("/health")
def health_check(request: Request):
    """
    Check API and database connectivity.
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
    List all books from the database.
    """
    with db.connect() as conn:
        result = conn.execute(text("SELECT * FROM books")).mappings().fetchall()
        return list(result)


@router.get("/books/search")
def search_books(title: str = Query(None), category: str = Query(None)):
    """
    Search books by title and/or category.
    """
    with db.connect() as conn:
        params = {}
        query = "SELECT * FROM books"
        if title:
            query = "SELECT * FROM books WHERE title LIKE :title"
            params["title"] = f"%{title}%"
        if category:
            query = "SELECT * FROM books WHERE category LIKE :category"
            params["category"] = f"%{category}%"
        result = conn.execute(text(query), params).mappings().fetchall()
        return list(result)


@router.get("/books/top-rated")
def top_rated_books():
    """
    List books with the highest ratings.
    """
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    id, title, Simbolo_Moeda || ' ' || price AS price, 
                    availability, rating, category, image_url
                FROM books
                ORDER BY 
                    CASE rating
                        WHEN 'One' THEN 1
                        WHEN 'Two' THEN 2
                        WHEN 'Three' THEN 3
                        WHEN 'Four' THEN 4
                        WHEN 'Five' THEN 5                   
                    END DESC
            """)).mappings().fetchall()
        return list(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/books/price-range")
def books_by_price_range(min: int = Query(0), max: int = Query(9999)):
    """
    Filter books within a specific price range.
    """
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM books
                WHERE price BETWEEN :min AND :max
            """), {"min": min, "max": max}).mappings().fetchall()
        return list(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/books/{book_id}")
def get_book(book_id: int):
    """
    Get a specific book by ID.
    """
    with db.connect() as conn:
        result = conn.execute(text("SELECT * FROM books WHERE id = :id"), {"id": book_id}).fetchone()
        if result:
            return dict(result)
        else:
            raise HTTPException(status_code=404, detail="Book not found")


@router.get("/categories")
def list_categories():
    """
    List all available book categories.
    """
    with db.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT category FROM books")).fetchall()
        return [row[0] for row in result if row[0]]


@router.get("/stats/overview")
def stats_overview():
    """
    Return collection overview: total books, average price, rating distribution.
    """
    try:
        with db.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) AS total_books,
                    Simbolo_Moeda || ' ' || ROUND(AVG(price), 2) AS avg_price,
                    SUM(CASE WHEN rating = 'One' THEN 1 ELSE 0 END) AS rating_One,
                    SUM(CASE WHEN rating = 'Two' THEN 1 ELSE 0 END) AS rating_Two,
                    SUM(CASE WHEN rating = 'Three' THEN 1 ELSE 0 END) AS rating_Three,
                    SUM(CASE WHEN rating = 'Four' THEN 1 ELSE 0 END) AS rating_Four,
                    SUM(CASE WHEN rating = 'Five' THEN 1 ELSE 0 END) AS rating_Five
                FROM books
            """)).mappings().first()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/categories")
def stats_by_category():
    """
    Return category-specific statistics (count and average price).
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


ep = ExecutePreprocessor(timeout=800, kernel_name='python3')


@router.post("/run-extraction")
@token_required
def run_extraction(request: Request):
    """
    Requires login token to execute.
    Runs the extract_books.py script and returns the generated CSV as a download.
    """
    script_path = os.path.join(os.path.dirname(__file__), "../extract/extract_books.py")
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_base/books.csv"))

    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Script extract_books.py not found.")

    try:
        result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=800)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Script execution error: {result.stderr}")

        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="CSV file was not generated.")

        return FileResponse(
            path=csv_path,
            filename="books.csv",
            media_type="text/csv"
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Script execution timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

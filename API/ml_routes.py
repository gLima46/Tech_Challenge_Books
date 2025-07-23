from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text

import pandas as pd
import sqlite3
import subprocess
import joblib
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

MODEL_PATH = os.path.join(ROOT_DIR, "ml", "modelo_gbp_blr.pkl")
GBP_SCRIPT_PATH = os.path.join(ROOT_DIR, "extract", "extract_gbp_today.py")
DB_PATH = os.path.join(ROOT_DIR, "data_base", "books.db")
FEATURES_DB_PATH = os.path.join(ROOT_DIR, "data_base", "features_books.db")
TRAINING_DB_PATH = os.path.join(ROOT_DIR, "data_base", "training_data.db")
TEST_DB_PATH = os.path.join(ROOT_DIR, "data_base", "teste_data.db")


model = joblib.load(MODEL_PATH)
model_df = model.history.copy()

db = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

from ml.data_processing import criar_banco_formatado

router = APIRouter(prefix="/ml", tags=["ML"])



class PurchaseRequest(BaseModel):
    book_name: str
    purchase_date: str  # Format: 'YYYY-MM-DD'



def save_to_db(df, db_path, table_name):
    """
    Save DataFrame to SQLite database, replacing the table if it exists.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()


def search_books(title: str):
    """
    Search for books by title.
    """
    with db.connect() as conn:
        if title:
            query = "SELECT * FROM books WHERE title LIKE :title"
            result = conn.execute(text(query), {"title": f"%{title}%"}).mappings().fetchall()
            return list(result)
        return []



@router.get("/features")
def get_ml_features():
    """
    Return formatted features for ML.
    """
    try:
        criar_banco_formatado()
        conn = sqlite3.connect(FEATURES_DB_PATH)
        df = pd.read_sql_query("SELECT * FROM features_books LIMIT 15", conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training-data-books")
def get_training_data():
    """
    Return training dataset and save to DB.
    """
    if not os.path.exists(FEATURES_DB_PATH):
        return Response(content="Database not found.", status_code=404)

    try:
        conn = sqlite3.connect(FEATURES_DB_PATH)
        df = pd.read_sql_query("SELECT * FROM features_books", conn)
        conn.close()
    except Exception as e:
        return Response(content=f"Error reading table: {e}", status_code=500)

    if df.empty:
        return Response(content="No data found in features_books.", status_code=404)

    df_sample = df.sample(frac=0.7, random_state=42).reset_index(drop=True)
    df_sample.to_csv("../data_base/training_data.csv", index=False)

    save_to_db(df_sample, TRAINING_DB_PATH, "training_books")

    return FileResponse(path="../data_base/training_data.csv", media_type='text/csv', filename="training_data.csv")


@router.get("/test-data-books")
def get_test_data():
    """
    Return test dataset and save to DB.
    """
    if not os.path.exists(FEATURES_DB_PATH):
        return Response(content="Database not found.", status_code=404)

    try:
        conn = sqlite3.connect(FEATURES_DB_PATH)
        df = pd.read_sql_query("SELECT * FROM features_books", conn)
        conn.close()
    except Exception as e:
        return Response(content=f"Error reading table: {e}", status_code=500)

    if df.empty:
        return Response(content="No data found in features_books.", status_code=404)

    df_sample = df.sample(frac=0.3, random_state=42).reset_index(drop=True)
    df_sample.to_csv("../data_base/test_data.csv", index=False)

    save_to_db(df_sample, TEST_DB_PATH, "test_books")

    return FileResponse(path="../data_base/test_data.csv", media_type='text/csv', filename="test_data.csv")

@router.get("/training-data-exchange")
def get_training_data():
    """
    Returns the training dataset for GBP to BRL exchange rate.
    """
    csv_path = "../data_base/training_price.csv"

    if not os.path.exists(csv_path):
        return Response(content="Arquivo CSV de treinamento não encontrado.", status_code=404)

    return FileResponse(path=csv_path, media_type='text/csv', filename="training_price.csv")

@router.post("/predictions")
def predict_book_price(req: PurchaseRequest):
    """
    Predict the price of a book on a future purchase date. Data format 'YYYY-MM-DD'
    """
    name = req.book_name.strip()
    purchase_date = pd.to_datetime(req.purchase_date)

    result = subprocess.run(["python", GBP_SCRIPT_PATH], capture_output=True, text=True, timeout=800)

    book = search_books(name)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found in database.")

    try:
        exchange_rate_str = result.stdout.strip()  # Ex: "7.50"
        exchange_rate = float(exchange_rate_str.replace(",", "."))
    except:
        raise HTTPException(status_code=500, detail="Error parsing exchange rate.")

    price_gbp = book[0]["price"]
    today_price_brl = round(price_gbp * exchange_rate, 2)

    future_days = (purchase_date - model_df['ds'].max()).days
    if future_days < 0:
        raise HTTPException(status_code=400, detail="Purchase date is in the past.")

    future_df = model.make_future_dataframe(periods=future_days + 1)
    forecast = model.predict(future_df)
    forecast['diff'] = abs(forecast['ds'] - purchase_date)
    closest_row = forecast.loc[forecast['diff'].idxmin()]
    predicted_rate = closest_row['yhat']
    predicted_price_brl = round(price_gbp * predicted_rate, 2)

    return {
        "book_name": book[0]["title"],
        "price_gbp": price_gbp,
        "today_exchange_rate": exchange_rate,
        "current_price_brl": today_price_brl,
        "purchase_date": purchase_date.strftime("%Y-%m-%d"),
        "predicted_exchange_rate": round(predicted_rate, 2),
        "predicted_price_brl_on_purchase_date": predicted_price_brl
    }

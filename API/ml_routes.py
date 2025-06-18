from fastapi import APIRouter, HTTPException
import pandas as pd
import sqlite3
import sys
import os

# Caminho absoluto para a raiz do projeto (um nível acima da pasta api/)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ml.data_processing import criar_banco_formatado


router = APIRouter(prefix="/ml", tags=["ML"])

@router.get("/features")
def get_ml_features():
    try:
        criar_banco_formatado()
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data_base/features_books.db'))
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM features_books LIMIT 5", conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import sqlite3
import pandas as pd
import os

def criar_banco_formatado():

    original_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data_base/books.db'))
    formatted_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data_base/features_books.db'))

    if os.path.exists(formatted_db_path):
        return

    if not os.path.exists(original_db_path):
        raise FileNotFoundError(f"Banco de dados original não encontrado em: {original_db_path}")


    conn_original = sqlite3.connect(original_db_path)
    df = pd.read_sql_query("SELECT * FROM books", conn_original)
    conn_original.close()

    if df.empty:
        raise ValueError("O banco de dados original está vazio ou a tabela 'books' não existe.")

    
    df_formatado = pd.DataFrame()
    df_formatado['id'] = df.index + 1  
    df_formatado['title'] = df['title']
    df_formatado['price'] = df['price'].astype(float)

    
    rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
    df_formatado['rating_numerical'] = df['rating'].map(rating_map)

    
    dummies = pd.get_dummies(df['category'])
    df_formatado = pd.concat([df_formatado, dummies], axis=1)

    
    conn_formatado = sqlite3.connect(formatted_db_path)
    df_formatado.to_sql('features_books', conn_formatado, index=False, if_exists='replace')
    conn_formatado.close()
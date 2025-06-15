import os
import sqlite3

# Caminho para a pasta onde o banco será salvo
db_dir = "data_base"
db_path = os.path.join(db_dir, "users.db")

# Cria a pasta se não existir
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Criação da base de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.close()
print(f"Banco de dados de usuários criado em: {db_path}")

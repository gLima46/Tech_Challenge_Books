import os
import sqlite3
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from functools import wraps
import jwt
from datetime import datetime, timedelta
import inspect

# Configurações
SECRET_KEY = "sua_chave_secreta_supersegura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 1800  # 30 minutos

# Caminhos
DB_DIR = os.path.join(os.path.dirname(__file__), "../data_base")
DB_PATH = os.path.join(DB_DIR, "users.db")

# Garante a existência do banco de dados e tabelas
def init_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        username TEXT,
        token TEXT,
        created_at DATETIME
    )
    """)

    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado em: {DB_PATH}")

# Inicializa o banco ao importar este módulo
init_db()

# FastAPI router
router = APIRouter(prefix="/auth", tags=["Auth"])

# MODELS
class Token(BaseModel):
    access_token: str
    token_type: str

class RegisterData(BaseModel):
    username: str
    password: str

class LoginData(BaseModel):
    username: str
    password: str

# HELPERS
def create_access_token(username: str):
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tokens (username, token, created_at) VALUES (?, ?, ?)", 
                   (username, token, datetime.utcnow()))
    conn.commit()
    conn.close()

    return token

def token_required(f):
    @wraps(f)
    async def decorated(request: Request, *args, **kwargs):
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Token ausente ou inválido (cookie)")

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("username")
            if username is None:
                raise HTTPException(status_code=401, detail="Token inválido")
            request.state.user = username
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Token inválido")

        if inspect.iscoroutinefunction(f):
            return await f(request, *args, **kwargs)
        else:
            return f(request, *args, **kwargs)

    return decorated

# ROTAS
@router.post("/register")
def register(data: RegisterData):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (data.username, data.password))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Usuário já existe")
    finally:
        conn.close()
    return {"message": "Usuário registrado com sucesso"}

@router.post("/login")
def login(data: LoginData, response: Response):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (data.username,))
    row = cursor.fetchone()
    conn.close()

    if not row or row[0] != data.password:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

    token = create_access_token(data.username)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_SECONDS
    )

    return {"message": "Login realizado com sucesso"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logout realizado com sucesso"}

@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido")

        new_token = create_access_token(username)

        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            samesite="strict",
            max_age=ACCESS_TOKEN_EXPIRE_SECONDS
        )

        return {"message": "Token renovado com sucesso"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

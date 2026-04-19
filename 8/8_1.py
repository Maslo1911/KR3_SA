import sqlite3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

DB_NAME = "users.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL,
            password TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()

app = FastAPI()

create_tables()

class User(BaseModel):
    username: str
    password: str

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: User):
    conn = get_db_connection()

    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (user.username, user.password),
    )
    conn.commit()
    conn.close()

    return {"message": "User registered successfully!"}
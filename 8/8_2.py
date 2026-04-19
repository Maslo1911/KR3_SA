import sqlite3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

DB_NAME = "todos.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT    NOT NULL,
            completed   INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

app = FastAPI(title="Todo API")

create_tables()

class TodoCreate(BaseModel):
    title: str
    description: str


class TodoUpdate(BaseModel):
    title: str
    description: str
    completed: bool


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

def get_todo_or_404(todo_id: int) -> TodoResponse:

    conn = get_db_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id={todo_id} not found",
        )

    return TodoResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        completed=bool(row["completed"]),
    )

@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate):
    conn = get_db_connection()

    cursor = conn.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, 0)",
        (todo.title, todo.description),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return TodoResponse(
        id=new_id,
        title=todo.title,
        description=todo.description,
        completed=False,
    )


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def read_todo(todo_id: int):
    return get_todo_or_404(todo_id)


@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate):
    get_todo_or_404(todo_id)

    conn = get_db_connection()
    conn.execute(
        """
        UPDATE todos
           SET title = ?, description = ?, completed = ?
         WHERE id = ?
        """,
        (todo.title, todo.description, int(todo.completed), todo_id),
    )
    conn.commit()
    conn.close()

    return TodoResponse(
        id=todo_id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
    )


@app.delete("/todos/{todo_id}", status_code=status.HTTP_200_OK)
def delete_todo(todo_id: int):
    get_todo_or_404(todo_id)

    conn = get_db_connection()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()

    return {"message": f"Todo {todo_id} deleted successfully"}


@app.get("/todos", response_model=list[TodoResponse])
def read_all_todos():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()

    return [
        TodoResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            completed=bool(row["completed"]),
        )
        for row in rows
    ]
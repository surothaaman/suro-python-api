from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from database import get_connection, initialize_database
import sqlite3

from schemas import UserCreate

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Suro User Management API",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {"message": "Suro Python API is running"}


@app.get("/api/v1/users")
def get_users():
    with get_connection() as connection:
        users = connection.execute(
            "SELECT id, name, email, created_at FROM users ORDER BY id"
        ).fetchall()

    return [dict(user) for user in users]
@app.post("/api/v1/users", status_code=201)
def create_user(user: UserCreate):
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                (user.name, str(user.email)),
            )

            created_user = connection.execute(
                """
                SELECT id, name, email, created_at
                FROM users
                WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        return dict(created_user)

    except sqlite3.IntegrityError as error:
        if error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            raise HTTPException(
                status_code=409,
                detail="A user with this email already exists.",
            ) from error
        raise
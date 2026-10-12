import sqlite3
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from schemas import UserCreate, UserUpdate

from database import get_connection, initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Suro User Management API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
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
    
@app.get("/api/v1/users/{user_id}")
def get_user(user_id: int):
    if user_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="User ID must be a positive number.",
        )

    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return dict(user)
@app.patch("/api/v1/users/{user_id}")
def update_user(user_id: int, changes: UserUpdate):
    if user_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="User ID must be a positive number.",
        )

    try:
        with get_connection() as connection:
            # Lock the write transaction before reading the existing user.
            connection.execute("BEGIN IMMEDIATE")

            existing_user = connection.execute(
                "SELECT id, name, email FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

            if existing_user is None:
                raise HTTPException(
                    status_code=404,
                    detail="User not found.",
                )

            updates = changes.model_dump(exclude_unset=True)

            name = updates.get("name", existing_user["name"])
            email = str(updates.get("email", existing_user["email"]))

            connection.execute(
                "UPDATE users SET name = ?, email = ? WHERE id = ?",
                (name, email, user_id),
            )

            updated_user = connection.execute(
                """
                SELECT id, name, email, created_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()

        return dict(updated_user)

    except sqlite3.IntegrityError as error:
        if error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            raise HTTPException(
                status_code=409,
                detail="A user with this email already exists.",
            ) from error
        raise
@app.delete("/api/v1/users/{user_id}")
def delete_user(user_id: int):
    if user_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="User ID must be a positive number.",
        )

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

    return {
        "message": "User deleted successfully.",
        "id": user_id,
    }

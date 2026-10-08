from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from database import get_connection, initialize_database


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
# Suro Python User Management API

A standalone REST API built with FastAPI and SQLite. It manages users through raw SQL and parameterized queries, without an ORM.

## Features

- List all users and retrieve a user by ID.
- Create users with name and email validation.
- Update a user's name, email, or both.
- Delete users by ID.
- Store records in a local SQLite database.
- Explore and test endpoints using interactive API documentation.

## Technology

- Python 3.11
- FastAPI and Uvicorn
- SQLite through Python's built-in sqlite3 module
- Pydantic and email-validator for request validation

## Project files

| File             | Purpose                                                                      |
| ---------------- | ---------------------------------------------------------------------------- |
| main.py          | Application startup, routes, SQL operations, and HTTP errors                 |
| database.py      | Database path, connection management, transactions, and table initialization |
| schemas.py       | UserCreate and UserUpdate request validation                                 |
| requirements.txt | Python dependencies                                                          |
| .gitignore       | Excludes local databases, environments, and secrets                          |
| README.md        | Setup, API usage, and testing instructions                                   |
| suro.db          | Local database created at startup; not committed to Git                      |
| venv/            | Local Python environment; not committed to Git                               |

## Setup on Windows

Open the project folder in VS Code. Run each command separately in PowerShell.

### Create a virtual environment

```powershell
python -m venv venv
```

### Install dependencies

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

If setting up without a requirements file:

```powershell
.\venv\Scripts\python.exe -m pip install fastapi uvicorn email-validator
```

Record installed versions after dependency changes:

```powershell
.\venv\Scripts\python.exe -m pip freeze > requirements.txt
```

### Start the development server

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

Keep this terminal running. Use a second terminal for Git commands.

- Home: http://127.0.0.1:8000/
- Interactive documentation: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

Press Ctrl + C to stop the server. The --reload option is for local development.

## Database

The application creates suro.db beside database.py on startup. This is separate from the Day 1 SQLite practice database.

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| Column     | Description                                            |
| ---------- | ------------------------------------------------------ |
| id         | Automatically generated primary key                    |
| name       | Required user name                                     |
| email      | Required, unique email                                 |
| created_at | Creation time, defaulting to the current UTC timestamp |

Records persist after the server stops. Successful database operations commit; failed operations roll back; connections close after use. PATCH uses a write transaction before reading and updating a user.

CREATE TABLE IF NOT EXISTS does not migrate an existing table. Future schema changes require a migration.

## Endpoints

Base URL: http://127.0.0.1:8000

| Method | Endpoint                | Purpose                  | Success status |
| ------ | ----------------------- | ------------------------ | -------------- |
| GET    | /                       | Check the API is running | 200            |
| GET    | /api/v1/users           | List users ordered by ID | 200            |
| GET    | /api/v1/users/{user_id} | Retrieve one user        | 200            |
| POST   | /api/v1/users           | Create a user            | 201            |
| PATCH  | /api/v1/users/{user_id} | Update selected fields   | 200            |
| DELETE | /api/v1/users/{user_id} | Delete a user            | 200            |

An empty user list returns [].

### Create a user

POST /api/v1/users

Set Content-Type to application/json.

```json
{
  "name": "Suro",
  "email": "suro@example.com"
}
```

The response contains id, name, email, and created_at. Use the returned ID for later requests.

### Update a user

PATCH /api/v1/users/{user_id}

Send one field or both:

```json
{
  "name": "Suro Updated"
}
```

Or:

```json
{
  "email": "suro.updated@example.com"
}
```

Omitted fields retain their existing values. The ID and creation timestamp remain unchanged.

### Delete a user

DELETE /api/v1/users/{user_id}

No request body is required. Example response when deleting ID 1:

```json
{
  "message": "User deleted successfully.",
  "id": 1
}
```

Deletion removes the record from the database.

## Validation and errors

- Creation requires name and email.
- Names are trimmed and must contain 1–100 characters.
- Email format is validated; this does not verify mailbox ownership or delivery.
- Unexpected request fields are rejected.
- PATCH requires at least one field and rejects explicit null values.
- User IDs must be positive integers.
- Duplicate emails are rejected by the database's UNIQUE constraint.
- The current schema does not enforce case-insensitive email uniqueness.

| Status | Meaning                              |
| ------ | ------------------------------------ |
| 200    | Successful read, update, or deletion |
| 201    | User created                         |
| 404    | User not found                       |
| 409    | Email already exists                 |
| 422    | Invalid request body or user ID      |

Example error:

```json
{
  "detail": "User not found."
}
```

Pydantic validation errors contain a structured detail array describing invalid fields.

## Raw SQL and parameterized queries

The project uses SELECT, INSERT, UPDATE, and DELETE directly.

Example:

```python
connection.execute(
    "SELECT id, name, email, created_at FROM users WHERE id = ?",
    (user_id,),
)
```

Values are bound separately from the SQL statement through ? placeholders. Do not concatenate user input into SQL. SQLite does not provide traditional stored procedures; application functions organize the SQL operations.

## Manual testing

Keep the server running and use Swagger /docs, Postman, or Bruno. For the course deliverable, perform the CRUD flow in Postman or Bruno as well.

1. POST a temporary user with a unique email; expect 201 and record its ID.
2. GET all users; confirm the temporary user appears.
3. GET the returned ID; expect 200 and the correct record.
4. PATCH only its name; confirm its email and created_at remain unchanged.
5. PATCH its email; confirm the new value using GET.
6. Restart the server and GET the user to verify persistence.
7. DELETE the temporary user; expect 200.
8. GET or DELETE the same ID again; expect 404.

Additional checks:

| Test                                          | Expected |
| --------------------------------------------- | -------- |
| Create a duplicate email                      | 409      |
| Change a user's email to another user's email | 409      |
| Create with a missing name or email           | 422      |
| Submit a blank name or invalid email          | 422      |
| PATCH with {} or an explicit null             | 422      |
| Submit an unexpected field                    | 422      |
| Use ID 0, a negative ID, or noninteger text   | 422      |

Use disposable users when testing DELETE.

## Git workflow

Save files before committing. Database files, virtual environments, and secrets must remain excluded by .gitignore.

Run commands separately:

```powershell
git status
git add main.py database.py schemas.py requirements.txt README.md .gitignore
git commit -m "Complete Python SQLite user CRUD API"
git push
```

The push command assumes a GitHub remote and upstream branch have already been configured. Commit and push completed work daily.

## Troubleshooting

### Missing email_validator

Install it using the project's Python interpreter, then restart the server:

```powershell
.\venv\Scripts\python.exe -m pip install email-validator
```

### Cannot import UserCreate or UserUpdate

Ensure schemas.py contains both class definitions and save the file.

### sqlite3 is not defined

Add import sqlite3 at the top of main.py.

### An endpoint is missing from /docs

Ensure its decorator and function start at the top level, outside other functions. Save, wait for the server reload, and refresh /docs.

### Not a Git repository

Run git init once inside the suro-python-api folder before staging and committing.

## Frontend Integration

The React client connects to this API using browser fetch requests.

CORS allows these development origins:

- http://localhost:5173
- http://127.0.0.1:5173

Allowed methods: GET, POST, PATCH and DELETE.
Allowed request header: Content-Type.

Manual browser testing completed:

- Create and list users.
- Edit users and confirm changes after refreshing.
- Delete users and confirm removal.

Both Python and Node.js backend flows were tested through the React
client without browser errors.

Python and Node.js use separate local SQLite databases.
CORS does not replace server-side validation or authentication.

## Scope

This is a local learning project built with FastAPI and SQLite.
It supports full user CRUD, server-side validation, parameterized SQL,
and CORS for the React client. Authentication and role management
are outside the project scope.

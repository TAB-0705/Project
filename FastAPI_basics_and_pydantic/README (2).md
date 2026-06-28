# To-Do CRUD API (FastAPI + Pydantic)

Clean-layered CRUD API: thin **router** → **service** (logic) → **repository**
(data access, isolated). In-memory store, so it runs with zero setup.

## Run (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive Swagger UI.

## Endpoints

| Method | Path           | Action            |
|--------|----------------|-------------------|
| POST   | /todos         | Create a todo     |
| GET    | /todos         | List all todos    |
| GET    | /todos/{id}    | Get one todo      |
| PUT    | /todos/{id}    | Update a todo     |
| DELETE | /todos/{id}    | Delete a todo     |

## Quick test (curl)

```bash
curl -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d "{\"title\": \"Buy milk\"}"
curl http://127.0.0.1:8000/todos
curl -X PUT http://127.0.0.1:8000/todos/1 -H "Content-Type: application/json" -d "{\"completed\": true}"
curl -X DELETE http://127.0.0.1:8000/todos/1
```

## Swapping to MongoDB later

Reimplement `app/repository.py` against a Motor collection. The service and
router depend only on the repository's method signatures, so nothing else
changes.

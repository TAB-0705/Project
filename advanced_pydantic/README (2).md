# Member Registration API — Advanced Pydantic Validators

Same clean layering as the To-Do app (router → service → repository), but the
entity carries strict business rules enforced entirely by **Pydantic
validators** instead of manual checks in route handlers.

## What the refactor demonstrates

| Rule                              | Where                          | Validator type        |
|-----------------------------------|--------------------------------|-----------------------|
| `member_id` matches `WNS-1234`    | `schemas.py`                   | `@field_validator`    |
| Email format (regex)              | `schemas.py`                   | `@field_validator`    |
| Phone format (regex)              | `schemas.py`                   | `@field_validator`    |
| Age >= 18 (from date of birth)    | `schemas.py`                   | `@field_validator`    |
| Password strength                 | `schemas.py`                   | `@field_validator`    |
| password == confirm_password      | `schemas.py`                   | `@model_validator`    |

Single-field rules use `@field_validator`; the cross-field rule needs the
whole object, so it uses `@model_validator(mode="after")`.

## Run (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Valid payload (POST /members)

```json
{
  "member_id": "WNS-0427",
  "full_name": "Tabri A",
  "email": "tabri@example.com",
  "phone": "+919876543210",
  "date_of_birth": "2000-05-01",
  "password": "Secret123",
  "confirm_password": "Secret123"
}
```

## Payloads that get rejected with 422 (try these in the demo)

- `member_id: "WN-12"` → bad ID format
- `date_of_birth: "2015-01-01"` → under 18
- `password: "short"` → too weak
- `confirm_password: "Different1"` → passwords don't match
```

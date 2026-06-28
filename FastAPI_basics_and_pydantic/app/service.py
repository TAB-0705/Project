from typing import Optional
from .repository import repository
from .schemas import TodoCreate, TodoUpdate


class TodoService:
    """Business logic. Knows nothing about HTTP — it returns data or None,
    and the router decides what status code that maps to. Keeping HTTP out
    of here is what lets the same logic be reused (e.g. from a CLI or tests).
    """

    def create(self, payload: TodoCreate) -> dict:
        return repository.create(payload.model_dump())

    def list_all(self) -> list[dict]:
        return repository.list_all()

    def get(self, todo_id: int) -> Optional[dict]:
        return repository.get(todo_id)

    def update(self, todo_id: int, payload: TodoUpdate) -> Optional[dict]:
        # exclude_unset → only the fields the client actually sent are changed
        changes = payload.model_dump(exclude_unset=True)
        return repository.update(todo_id, changes)

    def delete(self, todo_id: int) -> bool:
        return repository.delete(todo_id)


service = TodoService()

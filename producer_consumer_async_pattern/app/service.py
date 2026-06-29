from typing import Optional
from .repository import repository
from .schemas import TodoCreate, TodoUpdate
from . import event_publisher


class TodoService:
    """Business logic. `create` is async because it publishes an event to the
    queue after persisting — the producer side of the producer-consumer
    pattern. The other operations stay synchronous."""

    async def create(self, payload: TodoCreate) -> dict:
        todo = repository.create(payload.model_dump())
        # Fire the event AFTER the todo is safely stored.
        await event_publisher.publish_todo_created(todo)
        return todo

    def list_all(self) -> list[dict]:
        return repository.list_all()

    def get(self, todo_id: int) -> Optional[dict]:
        return repository.get(todo_id)

    def update(self, todo_id: int, payload: TodoUpdate) -> Optional[dict]:
        changes = payload.model_dump(exclude_unset=True)
        return repository.update(todo_id, changes)

    def delete(self, todo_id: int) -> bool:
        return repository.delete(todo_id)


service = TodoService()

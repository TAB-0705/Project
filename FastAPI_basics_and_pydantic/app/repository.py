from typing import Optional


class TodoRepository:
    """All data access lives here and ONLY here.

    It is in-memory for a zero-setup local demo, but the rest of the app
    only depends on these method signatures — not on a dict. To move to
    MongoDB/Motor later, you reimplement this class against a collection
    and nothing in the service or router has to change.
    """

    def __init__(self) -> None:
        self._items: dict[int, dict] = {}
        self._next_id: int = 1

    def create(self, data: dict) -> dict:
        item = {"id": self._next_id, **data}
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def list_all(self) -> list[dict]:
        return list(self._items.values())

    def get(self, todo_id: int) -> Optional[dict]:
        return self._items.get(todo_id)

    def update(self, todo_id: int, changes: dict) -> Optional[dict]:
        item = self._items.get(todo_id)
        if item is None:
            return None
        item.update(changes)
        return item

    def delete(self, todo_id: int) -> bool:
        return self._items.pop(todo_id, None) is not None


# Single shared instance for the app's lifetime.
repository = TodoRepository()

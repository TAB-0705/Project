from typing import Optional


class MemberRepository:
    """All data access isolated here. In-memory for a zero-setup demo;
    swap for MongoDB/Motor later without touching service or router."""

    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def exists(self, member_id: str) -> bool:
        return member_id in self._items

    def create(self, data: dict) -> dict:
        self._items[data["member_id"]] = data
        return data

    def list_all(self) -> list[dict]:
        return list(self._items.values())

    def get(self, member_id: str) -> Optional[dict]:
        return self._items.get(member_id)

    def delete(self, member_id: str) -> bool:
        return self._items.pop(member_id, None) is not None


repository = MemberRepository()

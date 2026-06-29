from typing import Optional
from .repository import repository
from .schemas import MemberCreate, compute_age


class DuplicateMemberError(Exception):
    """Raised when a member_id is already registered."""


class MemberService:
    """Logic only. Validation already happened in the Pydantic model by the
    time we get here, so this layer trusts the data and focuses on rules
    that need the data store (like uniqueness)."""

    def register(self, payload: MemberCreate) -> dict:
        if repository.exists(payload.member_id):
            raise DuplicateMemberError(payload.member_id)
        # Persist a safe record: drop passwords, add derived age.
        record = payload.model_dump(exclude={"password", "confirm_password"})
        record["age"] = compute_age(payload.date_of_birth)
        return repository.create(record)

    def list_all(self) -> list[dict]:
        return repository.list_all()

    def get(self, member_id: str) -> Optional[dict]:
        return repository.get(member_id)

    def delete(self, member_id: str) -> bool:
        return repository.delete(member_id)


service = MemberService()

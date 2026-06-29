from fastapi import APIRouter, HTTPException, status
from .schemas import MemberCreate, MemberResponse
from .service import service, DuplicateMemberError

router = APIRouter(prefix="/members", tags=["members"])


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def register_member(payload: MemberCreate):
    # If we reach here, all field/model validators have already passed.
    try:
        return service.register(payload)
    except DuplicateMemberError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="member_id already registered"
        )


@router.get("", response_model=list[MemberResponse])
def list_members():
    return service.list_all()


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: str):
    member = service.get(member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: str):
    if not service.delete(member_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")
    return None

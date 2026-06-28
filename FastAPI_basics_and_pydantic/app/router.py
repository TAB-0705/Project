from fastapi import APIRouter, HTTPException, status
from .schemas import TodoCreate, TodoUpdate, TodoResponse
from .service import service

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate):
    return service.create(payload)


@router.get("", response_model=list[TodoResponse])
def list_todos():
    return service.list_all()


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    todo = service.get(todo_id)
    if todo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, payload: TodoUpdate):
    todo = service.update(todo_id, payload)
    if todo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int):
    if not service.delete(todo_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return None

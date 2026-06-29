from pydantic import BaseModel, Field
from typing import Optional


class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Buy milk"])
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None


class TodoResponse(TodoBase):
    id: int

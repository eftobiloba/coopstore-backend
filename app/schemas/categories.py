from typing import List, Optional
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    id: int
    name: str


class CategoryCreate(BaseModel):
    name: str
    number: int
    image: str


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    number: Optional[int] = None
    image: Optional[str] = None


class CategoryOut(BaseModel):
    message: str
    data: CategoryBase


class CategoriesOut(BaseModel):
    message: str
    data: List[CategoryBase]


class CategoryDelete(BaseModel):
    id: int
    name: str


class CategoryOutDelete(BaseModel):
    message: str
    data: CategoryDelete

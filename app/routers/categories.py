from fastapi import APIRouter, Depends, Query, status
from typing import Any
from app.db.database import get_db
from app.services.categories import CategoryService
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.core.security import check_admin_role

router = APIRouter(tags=["Categories"], prefix="/categories")


# Get All Categories
@router.get("/", status_code=status.HTTP_200_OK,)
def get_all_categories(
    db: Any = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query("", description="Search based name of categories"),
):
    return CategoryService.get_all_categories(db, page, limit, search)


# Get Category By ID
@router.get("/{category_id}", status_code=status.HTTP_200_OK,)
def get_category(category_id: str, db: Any = Depends(get_db)):
    return CategoryService.get_category(db, category_id)


# Create New Category
@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_admin_role)])
def create_category(category: CategoryCreate, db: Any = Depends(get_db)):
    return CategoryService.create_category(db, category)


# Update Existing Category
@router.put("/{category_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_admin_role)])
def update_category(category_id: str, updated_category: CategoryUpdate, db: Any = Depends(get_db)):
    return CategoryService.update_category(db, category_id, updated_category)


# Delete Category By ID
@router.delete("/{category_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_admin_role)])
def delete_category(category_id: str, db: Any = Depends(get_db)):
    return CategoryService.delete_category(db, category_id)

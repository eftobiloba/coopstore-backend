from fastapi import APIRouter, Depends, Query, status
from typing import Any
from app.db.database import get_db
from app.services.users import UserService
from app.schemas.users import UserCreate, UserOut, UsersOut, UserOutDelete, UserUpdate
from app.core.security import check_admin_role

router = APIRouter(tags=["Users"], prefix="/users")


# Get All Users
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def get_all_users(
    db: Any = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query("", description="Search based username"),
    role: str = Query("user", enum=["user", "admin"])
):
    return UserService.get_all_users(db, page, limit, search, role)


# Get User By ID
@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def get_user(user_id: str, db: Any = Depends(get_db)):
    return UserService.get_user(db, user_id)


# Create New User
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_admin_role)]
)
def create_user(user: UserCreate, db: Any = Depends(get_db)):
    return UserService.create_user(db, user)


# Update Existing User
@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def update_user(user_id: str, updated_user: UserUpdate, db: Any = Depends(get_db)):
    return UserService.update_user(db, user_id, updated_user)


# Delete User By ID
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def delete_user(user_id: str, db: Any = Depends(get_db)):
    return UserService.delete_user(db, user_id)

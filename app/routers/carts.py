from fastapi import APIRouter, Depends, Query, status
from typing import Any
from app.db.database import get_db
from app.services.carts import CartService
from app.schemas.carts import CartCreate, CartUpdate, CartOut, CartOutDelete, CartsOutList
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

router = APIRouter(tags=["Carts"], prefix="/carts")
auth_scheme = HTTPBearer()


# Get All Carts
@router.get("/", status_code=status.HTTP_200_OK)
def get_all_carts(
    db: Any = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    print(token.credentials)
    return CartService.get_all_carts(db, token=token, page=page, limit=limit)


# Get Cart By User ID
@router.get("/{cart_id}", status_code=status.HTTP_200_OK)
def get_cart(
    cart_id: str,
    db: Any = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return CartService.get_cart(db, token=token, cart_id=cart_id)


# Create New Cart
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_cart(
    cart: CartCreate,
    db: Any = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return CartService.create_cart(db, token=token, cart=cart)


# Update Existing Cart
@router.put("/{cart_id}", status_code=status.HTTP_200_OK)
def update_cart(
    cart_id: str,
    updated_cart: CartUpdate,
    db: Any = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return CartService.update_cart(db, token=token, cart_id=cart_id, updated_cart=updated_cart)


# Delete Cart By User ID
@router.delete("/{cart_id}", status_code=status.HTTP_200_OK)
def delete_cart(
    cart_id: str,
    db: Any = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return CartService.delete_cart(db, token=token, cart_id=cart_id)

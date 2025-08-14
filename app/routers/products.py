from fastapi import APIRouter, Depends, Query, status
from app.db.database import get_db
from app.services.products import ProductService
from app.schemas.products import ProductCreate, ProductOut, ProductsOut, ProductOutDelete, ProductUpdate
from app.core.security import check_admin_role
from typing import Any

router = APIRouter(tags=["Products"], prefix="/products")


# Get All Products
@router.get("/", status_code=status.HTTP_200_OK)
def get_all_products(
    db: Any = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query("", description="Search based on product title"),
):
    return ProductService.get_all_products(db, page, limit, search)


# Get Product By ID
@router.get("/{product_id}", status_code=status.HTTP_200_OK)
def get_product(product_id: str, db: Any = Depends(get_db)):
    return ProductService.get_product(db, product_id)


# Create New Product
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_admin_role)]
)
def create_product(
    product: ProductCreate,
    db: Any = Depends(get_db)
):
    return ProductService.create_product(db, product)


# Update Existing Product
@router.put(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def update_product(
    product_id: str,
    updated_product: ProductUpdate,
    db: Any = Depends(get_db)
):
    return ProductService.update_product(db, product_id, updated_product)


# Delete Product By ID
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def delete_product(
    product_id: str,
    db: Any = Depends(get_db)
):
    return ProductService.delete_product(db, product_id)
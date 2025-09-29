from fastapi import APIRouter, status, Query
from app.services.scraping import ScrapingService

router = APIRouter(tags=["Scraping"], prefix="/scraping")

# Instantiate ScrapingService
scraper = ScrapingService()

# Get products via API call
@router.get("/products/{query}", status_code=status.HTTP_200_OK)
def get_product(query: str, page: int = Query(1, description="Page number for pagination (default: 1)")):
    return scraper.get_products(query=query, page=page)

# Get products from category
@router.get("/category/{category}", status_code=status.HTTP_200_OK)
def get_products_from_category(
    category: str,
    page: int = Query(1, description="Page number for pagination (default: 1)")
):
    return scraper.get_category(query=category, page=page)

# Get product detail from its page
@router.get("/products/url/{blob}", status_code=status.HTTP_200_OK)
def get_a_product_detail(blob: str):
    return scraper.get_product_details(blob)
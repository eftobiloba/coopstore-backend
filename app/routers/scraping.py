from fastapi import APIRouter, status, Query
from app.services.scraping import ScrapingService

router = APIRouter(tags=["Scraping"], prefix="/scraping")

# Instantiate ScrapingService
scraper = ScrapingService()

# Get products via API call
@router.get("/products/{query}", status_code=status.HTTP_200_OK)
def get_product(query: str, category: str = Query(..., description="Category to search (e.g., groceries, phones)")):
    return scraper.get_products(category=category, query=query)
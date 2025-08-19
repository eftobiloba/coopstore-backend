from bs4 import BeautifulSoup
import requests
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import logging
from app.schemas.products import ProductBase
from app.schemas.categories import CategoryBase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingService:
    def __init__(self):
        self.food_url = "https://www.supermart.ng"
        self.other_url = "https://www.jumia.com.ng"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
        }

    def get_food_products(self, query):
        if not query or not query.strip():
            logger.error("Query cannot be empty")
            return []

        url = f"{self.food_url}/search?options[prefix]=last&q={query.strip().replace(' ', '+')}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {str(e)}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        productlist = soup.find_all("li", {"class": "js-pagination-result"})

        if not productlist:
            logger.warning(f"No products found for query: {query}")
            return []

        products = []
        for index, product in enumerate(productlist):
            # Extract title
            title_element = product.find("p", {"class": "card__title"})
            title = title_element.find("a").text.strip() if title_element and title_element.find("a") else "Unknown Title"

            # Extract price
            price_element = product.find("span", {"class": "price__current"})
            price_ngn = 0
            if price_element:
                price_text = price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    price_ngn = int(float(price_text))
                except ValueError:
                    logger.warning(f"Invalid price format for product {title}: {price_text}")

            # Extract original price and calculate discount percentage
            original_price_element = product.find("s", {"class": "price__was"})
            original_price_ngn = 0
            if original_price_element:
                original_price_text = original_price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    original_price_ngn = int(float(original_price_text))
                except ValueError:
                    logger.warning(f"Invalid original price format for product {title}: {original_price_text}")

            discount_percentage = ((original_price_ngn - price_ngn) / original_price_ngn * 100) if original_price_ngn > 0 else 0

            # Extract image
            img_element = product.find("img", {"class": "img-fit img-fit--contain card__main-image"})
            thumbnail = ""
            if img_element:
                thumbnail = img_element.get("data-src") or img_element.get("src", "")
                if thumbnail.startswith("//"):
                    thumbnail = f"https:{thumbnail}"

            # Extract brand (infer from title or use default)
            brand = "Unknown"
            if "nini" in title.lower():
                brand = "Nini Foods"
            elif "okomu" in title.lower():
                brand = "Okomu"
            elif "maku" in title.lower():
                brand = "M'Aku"

            # Extract other fields
            rating = 0.0  # No rating data available
            product_id = index + 1  # Use index-based ID
            category_name = f"Food & Beverages/{query.strip().title()}"  # Derive from query
            category_obj = CategoryBase(id=index + 1, name=category_name)

            # Create product dictionary
            product_data = {
                "id": product_id,
                "blob": "-".join(title.lower().strip().split(" ")),
                "title": title,
                "description": None,
                "price": price_ngn,
                "discount_percentage": round(discount_percentage, 2),
                "rating": rating,
                "stock": 0,
                "brand": brand,
                "thumbnail": thumbnail,
                "images": [thumbnail] if thumbnail else [],
                "is_published": True,
                "type": "Food Products",
                "created_at": datetime.now(),
                "category_id": index + 1,
                "category": category_obj
            }

            # Validate and append to products list
            try:
                product_instance = ProductBase(**product_data)
                products.append(product_instance.dict())
            except ValueError as e:
                logger.error(f"Validation error for product {title}: {str(e)}")

        return products

    def get_other_products(self, query):
        if not query or not query.strip():
            logger.error("Query cannot be empty")
            return []

        url = f"{self.other_url}/catalog/?q={'+'.join(query.strip().lower().split())}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {str(e)}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        productlist = soup.find_all("article", {"class": "prd _fb col c-prd"})

        if not productlist:
            logger.warning(f"No products found for query: {query}")
            return []

        products = []
        for index, product in enumerate(productlist):
            data = product.find("a", {"class": "core"}) or product
            item_id = data.get("data-ga4-item_id", "")
            title = data.get("data-ga4-item_name", "") or "Unknown Title"
            brand = data.get("data-ga4-item_brand", "") or "Unknown Brand"

            # Extract price
            price_element = product.find("div", {"class": "prc"})
            price_ngn = 0
            if price_element:
                price_text = price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    price_ngn = int(float(price_text))
                except ValueError:
                    logger.warning(f"Invalid price format for product {title}: {price_element.text}")

            # Extract original price and calculate discount percentage
            original_price_element = product.find("div", {"class": "old"})
            original_price_ngn = 0
            if original_price_element:
                original_price_text = original_price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    original_price_ngn = int(float(original_price_text))
                except ValueError:
                    logger.warning(f"Invalid original price format for product {title}: {original_price_element.text}")

            discount_percentage = ((original_price_ngn - price_ngn) / original_price_ngn * 100) if original_price_ngn > 0 else 0

            # Extract image
            img_element = product.find("div", {"class": "img-c"}).find("img") if product.find("div", {"class": "img-c"}) else None
            thumbnail = img_element.get("data-src", "") if img_element else ""

            # Extract rating
            rating_str = data.get("data-gtm-dimension27", "")
            try:
                rating = float(rating_str) if rating_str else 0.0
            except ValueError:
                logger.warning(f"Invalid rating format for product {title}: {rating_str}")
                rating = 0.0

            # Extract other fields
            category_path = data.get("data-ga4-item_category", "")
            category_path2 = data.get("data-ga4-item_category2", "")
            category_path3 = data.get("data-ga4-item_category3", "")
            category_path4 = data.get("data-ga4-item_category4", "")
            category_name = f"{category_path}/{category_path2}/{category_path3}/{category_path4}".strip("/") or query.strip().title()
            category_obj = CategoryBase(id=index + 1, name=category_name)

            # Handle item_id
            product_id = index + 1
            if item_id:
                cleaned_id = item_id.replace("NAFAMZ", "")
                if cleaned_id.isdigit():
                    product_id = int(cleaned_id)
                else:
                    logger.warning(f"Non-numeric item_id for product {title}: {cleaned_id}")

            # Create product dictionary
            product_data = {
                "id": product_id,
                "blob": None,
                "title": title,
                "description": None,
                "price": price_ngn,
                "discount_percentage": round(discount_percentage, 2),
                "rating": rating,
                "stock": 0,
                "brand": brand,
                "thumbnail": thumbnail,
                "images": [thumbnail] if thumbnail else [],
                "is_published": True,
                "type": category_path3 or "Products",
                "created_at": datetime.now(),
                "category_id": index + 1,
                "category": category_obj
            }

            # Validate and append to products list
            try:
                product_instance = ProductBase(**product_data)
                products.append(product_instance.dict())
            except ValueError as e:
                logger.error(f"Validation error for product {title}: {str(e)}")

        return products

    def get_products(self, category, query):
        if not category or not query or not category.strip() or not query.strip():
            logger.error("Category and query cannot be empty")
            return []

        # Check if category is food-related
        food_keywords = ["food", "groceries", "beverages", "snacks", "cooking", "drinks"]
        is_food_category = any(keyword in category.lower() for keyword in food_keywords)

        if is_food_category:
            logger.info(f"Routing food category '{category}' to get_food_products with query '{query}'")
            return self.get_food_products(query)
        else:
            logger.info(f"Routing non-food category '{category}' to get_other_products with query '{query}'")
            return self.get_other_products(query)
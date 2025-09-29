import json
import re
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

    def parse_food_html(self, html: str, query: str) -> list:
        """
        Parse Supermart/food search HTML and return a list of product dicts.
        """
        soup = BeautifulSoup(html, 'html.parser')
        productlist = soup.find_all("li", {"class": "js-pagination-result"})

        if not productlist:
            logger.warning(f"No food products found in HTML for query: {query}")
            return []

        products = []
        for index, product in enumerate(productlist):
            # ✅ Title + URL
            title_element = product.find("p", {"class": "card__title"})
            title = title_element.find("a").text.strip() if title_element and title_element.find("a") else "Unknown Title"
            relative_url = title_element.find("a").get("href", "") if title_element and title_element.find("a") else ""

            # ✅ Price
            price_ngn = 0
            price_element = product.find("span", {"class": "price__current"})
            if price_element:
                price_text = price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    price_ngn = int(float(price_text))
                except ValueError:
                    logger.warning(f"Invalid price format for {title}: {price_text}")

            # ✅ Old price + discount %
            original_price_ngn = 0
            original_price_element = product.find("s", {"class": "price__was"})
            if original_price_element:
                original_price_text = original_price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    original_price_ngn = int(float(original_price_text))
                except ValueError:
                    logger.warning(f"Invalid original price format for {title}: {original_price_text}")

            discount_percentage = (
                (original_price_ngn - price_ngn) / original_price_ngn * 100
                if original_price_ngn > 0 else 0
            )

            # ✅ Image
            thumbnail = ""
            img_element = product.find("img", {"class": "img-fit img-fit--contain card__main-image"})
            if img_element:
                thumbnail = img_element.get("data-src") or img_element.get("src", "")
                if thumbnail.startswith("//"):
                    thumbnail = f"https:{thumbnail}"

            # ✅ Brand inference
            brand = "Unknown"
            lower_title = title.lower()
            if "nini" in lower_title:
                brand = "Nini Foods"
            elif "okomu" in lower_title:
                brand = "Okomu"
            elif "maku" in lower_title:
                brand = "M'Aku"

            # ✅ Build category
            category_name = f"Food & Beverages/{query.strip().title()}"
            category_obj = CategoryBase(id=index + 1, name=category_name)

            # ✅ Build product dictionary
            product_id = index + 1
            blob = relative_url.split("/")[2] if relative_url and "/" in relative_url else f"food-{product_id}"

            product_data = {
                "id": product_id,
                "blob": blob,
                "title": title,
                "description": None,
                "price": price_ngn,
                "discount_percentage": round(discount_percentage, 2),
                "rating": 0.0,  # No rating data on Supermart
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

            # ✅ Validate & append
            try:
                product_instance = ProductBase(**product_data)
                products.append(product_instance.dict())
            except ValueError as e:
                logger.error(f"Validation error for food product {title}: {str(e)}")

        return products

    def get_products(self, query, page: int = 1):
        if not query or not query.strip():
            logger.error("Query cannot be empty")
            return []
        
        jumia_url = f"https://www.jumia.com.ng/catalog/?q={'+'.join(query.strip().lower().split())}"
        supermart_url = f"https://www.supermart.ng/search?options[prefix]=last&q={query.strip().replace(' ', '+')}"

        try:
            if page > 1:
                jumia_url += f"/?page={page}#catalog-listing"
            response = requests.get(jumia_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            products = self.parse_jumia_listing_html(response.text, jumia_url)

            if not products:  # ✅ nothing found → try Supermart
                logger.warning(f"No products parsed from Jumia for {query}, trying Supermart...")
                if page > 1:
                    supermart_url += f"/?page={page}"
                try:
                    response = requests.get(supermart_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    return self.parse_food_html(response.text, supermart_url)
                except requests.RequestException as e2:
                    logger.error(f"Failed to fetch Supermart {supermart_url}: {str(e2)}")
                    return []
            return products

        except requests.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"Jumia returned 404 for {jumia_url}, trying Supermart...")
                try:
                    if page > 1:
                        supermart_url += f"/?page={page}"
                    response = requests.get(supermart_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    return self.parse_food_html(response.text, supermart_url)
                except requests.RequestException as e2:
                    logger.error(f"Failed to fetch Supermart {supermart_url}: {str(e2)}")
                    return []
            else:
                logger.error(f"Failed to fetch Jumia {jumia_url}: {str(e)}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Jumia {jumia_url}: {str(e)}")
            return []

        
    def parse_jumia_listing_html(self, html: str, query: str) -> list:
        """
        Parse Jumia category/search HTML and return a list of product dicts.
        """
        soup = BeautifulSoup(html, 'html.parser')
        productlist = soup.find_all("article", {"class": "prd _fb col c-prd"})

        if not productlist:
            logger.warning(f"No products found in HTML for query: {query}")
            return []

        products = []
        for index, product in enumerate(productlist):
            data = product.find("a", {"class": "core"}) or product
            item_id = data.get("data-ga4-item_id", "")
            title = data.get("data-ga4-item_name", "") or "Unknown Title"
            brand = data.get("data-ga4-item_brand", "") or "Unknown Brand"

            # ✅ Product URL
            relative_url = data.get("href", "")
            product_url = f"https://www.jumia.com.ng{relative_url}" if relative_url else ""

            # ✅ Price
            price_ngn = 0
            price_element = product.find("div", {"class": "prc"})
            if price_element:
                price_text = price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    price_ngn = int(float(price_text))
                except ValueError:
                    logger.warning(f"Invalid price format for {title}: {price_element.text}")

            # ✅ Old price + discount %
            original_price_ngn = 0
            original_price_element = product.find("div", {"class": "old"})
            if original_price_element:
                original_price_text = original_price_element.text.strip().replace("₦", "").replace(",", "").strip()
                try:
                    original_price_ngn = int(float(original_price_text))
                except ValueError:
                    logger.warning(f"Invalid original price format for {title}: {original_price_element.text}")

            discount_percentage = (
                (original_price_ngn - price_ngn) / original_price_ngn * 100
                if original_price_ngn > 0 else 0
            )

            # ✅ Image
            thumbnail = ""
            img_container = product.find("div", {"class": "img-c"})
            if img_container:
                img_elem = img_container.find("img")
                if img_elem:
                    thumbnail = img_elem.get("data-src", "")

            # ✅ Rating
            rating_str = data.get("data-gtm-dimension27", "")
            try:
                rating = float(rating_str) if rating_str else 0.0
            except ValueError:
                logger.warning(f"Invalid rating format for {title}: {rating_str}")
                rating = 0.0

            # ✅ Category path
            category_path = data.get("data-ga4-item_category", "")
            category_path2 = data.get("data-ga4-item_category2", "")
            category_path3 = data.get("data-ga4-item_category3", "")
            category_path4 = data.get("data-ga4-item_category4", "")
            category_name = f"{category_path}/{category_path2}/{category_path3}/{category_path4}".strip("/") or query.strip().title()

            category_obj = CategoryBase(id=index + 1, name=category_name)

            # ✅ Product ID from Jumia (cleaning)
            product_id = index + 1
            if item_id:
                cleaned_id = item_id.replace("NAFAMZ", "")
                if cleaned_id.isdigit():
                    product_id = int(cleaned_id)
                else:
                    logger.warning(f"Non-numeric item_id for {title}: {cleaned_id}")

            # ✅ Build product dictionary
            blob_match = re.search(r'/([^/]+)\.html$', product_url)
            blob = blob_match.group(1) if blob_match else f"prod-{product_id}"

            product_data = {
                "id": product_id,
                "blob": blob,
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

            try:
                product_instance = ProductBase(**product_data)
                products.append(product_instance.dict())
            except ValueError as e:
                logger.error(f"Validation error for product {title}: {str(e)}")

        return products
    
    def get_category(self, query, page: int = 1):
        if not query or not query.strip():
            logger.error("Query cannot be empty")
            return []
        
        jumia_url = f"https://www.jumia.com.ng/{query}/"
        supermart_url = f"https://www.supermart.ng/collections/{query}"

        try:
            if page > 1:
                jumia_url += f"/?page={page}#catalog-listing"
            response = requests.get(jumia_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            products = self.parse_jumia_listing_html(response.text, jumia_url)

            # ✅ Jumia returned 200 but no products found → fallback to Supermart
            if not products:
                logger.warning(f"No products parsed from Jumia category {query}, trying Supermart...")
                if page > 1:
                    supermart_url += f"/?page={page}"
                try:
                    response = requests.get(supermart_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    return self.parse_food_html(response.text, supermart_url)
                except requests.RequestException as e2:
                    logger.error(f"Failed to fetch Supermart category {supermart_url}: {str(e2)}")
                    return []

            return products

        except requests.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"Jumia returned 404 for {jumia_url}, trying Supermart...")
                try:
                    if page > 1:
                        supermart_url += f"/?page={page}"
                    response = requests.get(supermart_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    return self.parse_food_html(response.text, supermart_url)
                except requests.RequestException as e2:
                    logger.error(f"Failed to fetch Supermart category {supermart_url}: {str(e2)}")
                    return []
            else:
                logger.error(f"Failed to fetch Jumia category {jumia_url}: {str(e)}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Jumia category {jumia_url}: {str(e)}")
            return []


    def _parse_jumia_product(self, html: str, url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        # ✅ Title
        title = soup.find("h1")
        title = title.text.strip() if title else "Unknown Title"

        # ✅ Brand
        brand = None
        brand_elem = soup.find("div", class_="-pvxs")
        if brand_elem:
            brand_link = brand_elem.find("a")
            if brand_link:
                brand = brand_link.text.strip()

        # ✅ Price, Old Price, Discount
        price_elem = soup.find("span", class_="-b -ubpt -tal -fs24 -prxs")
        price = self._parse_price(price_elem.text) if price_elem else 0

        old_price_elem = soup.find("span", class_="-tal -gy5 -lthr -fs16 -pvxs -ubpt")
        old_price = self._parse_price(old_price_elem.text) if old_price_elem else 0

        discount_elem = soup.find("span", class_="bdg _dsct _dyn -mls")
        discount = discount_elem.text.strip() if discount_elem else None

        # ✅ Stock info
        stock_info = None
        stock_elem = soup.find("p", class_="-df -i-ctr -fs12 -pbs -yl7")
        if stock_elem:
            stock_info = stock_elem.text.strip()

        # ✅ Shipping info
        shipping_info = None
        ship_elem = soup.find("div", class_="markup -fs12 -pbs")
        if ship_elem:
            shipping_info = ship_elem.text.strip()

        # ✅ Rating + Reviews
        rating = 0.0
        reviews_count = 0
        rating_elem = soup.find("div", class_="stars _m _al")
        if rating_elem:
            try:
                rating_text = rating_elem.text.strip().split("out of")[0]
                rating = float(rating_text)
            except Exception:
                pass
            review_link = soup.find("a", href=lambda href: href and "productratingsreviews" in href)
            if review_link:
                try:
                    reviews_count = int(review_link.text.strip().split()[0].replace("(", "").replace(")", ""))
                except Exception:
                    pass

        # ✅ Images
        images = []
        img_slider = soup.find("div", id="imgs")
        if img_slider:
            img_tags = img_slider.find_all("a", class_="itm")
            for tag in img_tags:
                img_url = tag.get("href")
                if img_url:
                    images.append(img_url)

        # ✅ Description
        description = None
        desc_elem = soup.find("div", id="description")
        if desc_elem:
            markup = desc_elem.find_next("div", class_="markup")
            if markup:
                description = markup.get_text(separator="\n").strip()

        # ✅ Key Features
        key_features = []
        key_elem = soup.find("h2", text="Key Features")
        if key_elem:
            ul = key_elem.find_next("div", class_="markup")
            if ul:
                key_features = [li.text.strip() for li in ul.find_all("li")]

        # ✅ What’s in the box
        whats_in_box = None
        box_elem = soup.find("h2", text="What’s in the box")
        if box_elem:
            box_div = box_elem.find_next("div", class_="markup")
            if box_div:
                whats_in_box = box_div.get_text(separator="\n").strip()

        # ✅ Specifications
        specifications = {}
        spec_section = soup.find("div", id="specifications")
        if spec_section:
            items = spec_section.find_all("li", class_="-pvxs")
            for li in items:
                key_span = li.find("span", class_="-b")
                if key_span:
                    key = key_span.text.strip().replace(":", "")
                    val = li.text.replace(key_span.text, "").strip().strip(":")
                    specifications[key] = val

        # ✅ Build final product JSON
        product_data = {
            "url": url,
            "title": title,
            "brand": brand,
            "price": price,
            "old_price": old_price,
            "discount": discount,
            "stock_info": stock_info,
            "shipping_info": shipping_info,
            "rating": rating,
            "reviews_count": reviews_count,
            "images": images,
            "description": description,
            "key_features": key_features,
            "whats_in_box": whats_in_box,
            "specifications": specifications,
        }

        return product_data
    
    def _parse_supermart_product(self, html: str, url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        # ✅ Title
        title_elem = soup.find("h1", class_="product-title")
        title = title_elem.text.strip() if title_elem else "Unknown Title"

        # ✅ Brand
        brand_elem = soup.find("span", class_="product-vendor")
        brand = brand_elem.text.strip() if brand_elem else "Unknown Brand"

        # ✅ Price
        price_elem = soup.find("span", class_="price__current")
        price = self._parse_price(price_elem.text) if price_elem else 0

        # ✅ Old price (if available)
        old_price_elem = soup.find("s")
        old_price = self._parse_price(old_price_elem.text) if old_price_elem else 0

        # ✅ Images
        images = []
        img_elem = soup.find("a", class_="media--cover")
        if img_elem and img_elem.get("href"):
            images.append("https:" + img_elem["href"])

        # ✅ Stock (Supermart uses Shopify inventory JSON)
        stock = None
        inv_data = soup.find("script", class_="js-inventory-data")
        if inv_data:
            try:
                stock_json = json.loads(inv_data.string)
                stock = stock_json[0].get("inventory_quantity", None)
            except Exception:
                pass

        # ✅ Fallback description
        description = f"Get {title} from Rapport CoopStore. High quality product available for you."

        # ✅ Build product data
        product_data = {
            "url": url,
            "title": title,
            "brand": brand,
            "price": price,
            "old_price": old_price,
            "discount": None,   # Supermart doesn’t show % discount
            "stock_info": stock,
            "shipping_info": None,
            "rating": 0.0,      # Not available
            "reviews_count": 0, # Not available
            "images": images,
            "description": description,
            "key_features": [],
            "whats_in_box": None,
            "specifications": {},
        }

        return product_data

    def get_product_details(self, url: str):
        jumia_url = f"https://www.jumia.com.ng/{url}.html"
        supermart_url = f"https://www.supermart.ng/products/{url}"

        try:
            response = requests.get(jumia_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return self._parse_jumia_product(response.text, jumia_url)

        except requests.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"Jumia returned 404 for {jumia_url}, trying Supermart...")
                try:
                    response = requests.get(supermart_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    return self._parse_supermart_product(response.text, supermart_url)
                except requests.RequestException as e2:
                    logger.error(f"Failed to fetch product page {supermart_url}: {str(e2)}")
                    return {}
            else:
                logger.error(f"Failed to fetch product page {jumia_url}: {str(e)}")
                return {}
        except requests.RequestException as e:
            logger.error(f"Failed to fetch product page {jumia_url}: {str(e)}")
            return {}

    # helper method for parsing prices
    def _parse_price(self, price_str: str) -> int:
        if not price_str:
            return 0
        clean = price_str.replace("₦", "").replace(",", "").strip()
        try:
            return int(float(clean))
        except ValueError:
            return 0

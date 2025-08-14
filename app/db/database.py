from typing import Generator
from app.core.config import settings
from pymongo import MongoClient
import certifi

# MongoDB connection setup
DATABASE_URL = settings.mongodb_uri
ca = certifi.where()

client = MongoClient(DATABASE_URL, tls=True, tlsCAFile=ca)
mongo_db = client.store_db  # renamed from `db` to avoid confusion

# Collections
users_collection = mongo_db["user_collection"]
membership_applications_collection = mongo_db["membership_applications_collection"]
products_collection = mongo_db["products_collection"]
categories_collection = mongo_db["categories_collection"]
financial_products_collection = mongo_db["financial_products_collection"]
carts_collection = mongo_db["carts_collection"]
cart_items_collection = mongo_db["cart_items_collection"]
orders_collection = mongo_db["orders_collection"]
bnpl_applications_collection = mongo_db["bnpl_applications_collection"]
reviews_collection = mongo_db["reviews_collection"]
promo_banners_collection = mongo_db["promo_banners_collection"]

# Indexes
# users_collection.create_index("coop_id", unique=True)

# Dependency for FastAPI
def get_db() -> Generator:
    """
    FastAPI dependency that yields the MongoDB database.
    Keeps a single global client alive.
    """
    try:
        yield mongo_db
    finally:
        # We don't close the client here to keep the connection pooled.
        pass

from bson import ObjectId
from app.utils.responses import ResponseHandler
from app.schemas.products import ProductCreate, ProductUpdate
from app.services.helpers import blob_generator, serialize_doc, array_serialize_doc

class ProductService:
    def __init__(self, db):
        # db is your MongoDB database instance (not a session)
        self.products = db["products_collection"]
        self.categories = db["categories_collection"]

    def get_all_products(self, page: int, limit: int, search: str = ""):
        query = {}
        if search:
            query["title"] = {"$regex": search, "$options": "i"}

        cursor = self.products.find(query).sort("_id", 1).skip((page - 1) * limit).limit(limit)
        products = list(cursor)

        return {
            "message": f"Page {page} with {limit} products",
            "data": array_serialize_doc(products)
        }

    def get_product(self, product_id: str):
        product = self.products.find_one({"blob": product_id})
        if not product:
            ResponseHandler.not_found_error("Product", product_id)
        return ResponseHandler.get_single_success(product["title"], str(product["_id"]), serialize_doc(product))

    def create_product(self, product: ProductCreate):
        category_exists = self.categories.find_one({"number": product.category_id})
        if not category_exists:
            ResponseHandler.not_found_error("Category", product.category_id)

        product_dict = product.model_dump()
        product_dict["blob"] = blob_generator(product_dict["title"])

        result = self.products.insert_one(product_dict)
        new_product = self.products.find_one({"_id": ObjectId(result.inserted_id)})

        return ResponseHandler.create_success(new_product["title"], str(new_product["_id"]), serialize_doc(new_product))

    def update_product(self, product_id: str, updated_product: ProductUpdate):
        product_exists = self.products.find_one({"blob": product_id})
        if not product_exists:
            ResponseHandler.not_found_error("Product", product_id)

        update_data = {k: v for k, v in updated_product.model_dump().items() if v is not None}
        if "category_id" in update_data:
            update_data["category_id"] = ObjectId(update_data["category_id"])

        self.products.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
        updated = self.products.find_one({"_id": ObjectId(product_id)})

        return ResponseHandler.update_success(updated["title"], str(updated["_id"]), serialize_doc(updated))

    def delete_product(self, product_id: str):
        product = self.products.find_one({"blob": product_id})
        if not product:
            ResponseHandler.not_found_error("Product", product_id)

        self.products.delete_one({"_id": ObjectId(product_id)})
        return ResponseHandler.delete_success(product["title"], str(product["_id"]), serialize_doc(product))
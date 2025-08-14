from bson import ObjectId
from app.utils.responses import ResponseHandler
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.services.helpers import serialize_doc, array_serialize_doc


class CategoryService:
    def __init__(self, db):
        # db is your MongoDB database instance
        self.categories = db["categories_collection"]

    def get_all_categories(self, page: int, limit: int, search: str = ""):
        query = {}
        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        cursor = (
            self.categories.find(query)
            .sort("_id", 1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        categories = array_serialize_doc(cursor)
        return {
            "message": f"Page {page} with {limit} categories",
            "data": categories
        }

    def get_category(self, category_id: str):
        try:
            oid = ObjectId(category_id)
        except:
            return ResponseHandler.not_found_error("Category", category_id)

        category = self.categories.find_one({"_id": oid})
        if not category:
            return ResponseHandler.not_found_error("Category", category_id)

        return ResponseHandler.get_single_success(category["name"], str(category["_id"]), serialize_doc(category))

    def create_category(self, category: CategoryCreate):
        category_dict = category.model_dump()
        result = self.categories.insert_one(category_dict)
        new_category = self.categories.find_one({"_id": result.inserted_id})

        return ResponseHandler.create_success(new_category["name"], str(new_category["_id"]), serialize_doc(new_category))

    def update_category(self, category_id: str, updated_category: CategoryUpdate):
        try:
            oid = ObjectId(category_id)
        except:
            return ResponseHandler.not_found_error("Category", category_id)

        category_exists = self.categories.find_one({"_id": oid})
        if not category_exists:
            return ResponseHandler.not_found_error("Category", category_id)

        update_data = {k: v for k, v in updated_category.model_dump().items() if v is not None}

        self.categories.update_one({"_id": oid}, {"$set": update_data})
        updated = self.categories.find_one({"_id": oid})

        return ResponseHandler.update_success(updated["name"], str(updated["_id"]), serialize_doc(updated))

    def delete_category(self, category_id: str):
        try:
            oid = ObjectId(category_id)
        except:
            return ResponseHandler.not_found_error("Category", category_id)

        category = self.categories.find_one({"_id": oid})
        if not category:
            return ResponseHandler.not_found_error("Category", category_id)

        self.categories.delete_one({"_id": oid})
        return ResponseHandler.delete_success(category["name"], str(category["_id"]), serialize_doc(category))

from bson import ObjectId
from app.utils.responses import ResponseHandler
from app.schemas.users import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.services.helpers import serialize_doc, array_serialize_doc

class UserService:
    def __init__(self, db):
        # db is your MongoDB database instance
        self.users = db["user_collection"]

    def get_all_users(self, page: int, limit: int, search: str = "", role: str = "user"):
        query = {"role": role}
        if search:
            query["username"] = {"$regex": search, "$options": "i"}

        cursor = (
            self.users.find(query)
            .sort("_id", 1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        users = array_serialize_doc(cursor)

        return {
            "message": f"Page {page} with {limit} users",
            "data": users
        }

    def get_user(self, user_id: str):
        try:
            oid = ObjectId(user_id)
        except:
            return ResponseHandler.not_found_error("User", user_id)

        user = self.users.find_one({"_id": oid})
        if not user:
            return ResponseHandler.not_found_error("User", user_id)

        return ResponseHandler.get_single_success(user.get("username"), str(user["_id"]), serialize_doc(user))

    def create_user(self, user: UserCreate):
        hashed_password = get_password_hash(user.password)
        user_dict = user.model_dump()
        user_dict["password"] = hashed_password

        result = self.users.insert_one(user_dict)
        new_user = self.users.find_one({"_id": result.inserted_id})

        return ResponseHandler.create_success(new_user["username"], str(new_user["_id"]), serialize_doc(new_user))

    def update_user(self, user_id: str, updated_user: UserUpdate):
        try:
            oid = ObjectId(user_id)
        except:
            return ResponseHandler.not_found_error("User", user_id)

        user_exists = self.users.find_one({"_id": oid})
        if not user_exists:
            return ResponseHandler.not_found_error("User", user_id)

        update_data = {k: v for k, v in updated_user.model_dump().items() if v is not None}

        # Hash password if updated
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])

        self.users.update_one({"_id": oid}, {"$set": update_data})
        updated = self.users.find_one({"_id": oid})

        return ResponseHandler.update_success(updated["username"], str(updated["_id"]), serialize_doc(updated))

    def delete_user(self, user_id: str):
        try:
            oid = ObjectId(user_id)
        except:
            return ResponseHandler.not_found_error("User", user_id)

        user = self.users.find_one({"_id": oid})
        if not user:
            return ResponseHandler.not_found_error("User", user_id)

        self.users.delete_one({"_id": oid})
        return ResponseHandler.delete_success(user["username"], str(user["_id"]), serialize_doc(user))

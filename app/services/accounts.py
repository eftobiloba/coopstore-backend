from bson import ObjectId
from app.utils.responses import ResponseHandler
from app.core.security import get_password_hash, get_token_payload
from app.services.helpers import serialize_doc, array_serialize_doc


class AccountService:
    def __init__(self, db):
        # db is your MongoDB database instance
        self.users = db["user_collection"]

    def get_my_info(self, token):
        user_id = get_token_payload(token.credentials).get("id")

        try:
            oid = ObjectId(user_id)
        except:
            return ResponseHandler.not_found_error("User", user_id)

        user = self.users.find_one({"_id": oid})
        if not user:
            return ResponseHandler.not_found_error("User", user_id)

        return ResponseHandler.get_single_success(user.get("username"), str(user["_id"]), serialize_doc(user))

    def edit_my_info(self, token, updated_user):
        user_id = get_token_payload(token.credentials).get("id")

        try:
            oid = ObjectId(user_id)
        except:
            return ResponseHandler.not_found_error("User", user_id)

        user_exists = self.users.find_one({"_id": oid})
        if not user_exists:
            return ResponseHandler.not_found_error("User", user_id)

        update_data = {k: v for k, v in updated_user.model_dump().items() if v is not None}

        # If password change is allowed, hash it before saving
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])

        self.users.update_one({"_id": oid}, {"$set": update_data})
        updated = self.users.find_one({"_id": oid})

        return ResponseHandler.update_success(updated.get("username"), str(updated["_id"]), serialize_doc(updated))

    def remove_my_account(self, token):
        user_id = get_token_payload(token.credentials).get("id")

        try:
            oid = ObjectId(user_id)
        except:
            return ResponseHandler.not_found_error("User", user_id)

        user = self.users.find_one({"_id": oid})
        if not user:
            return ResponseHandler.not_found_error("User", user_id)

        self.users.delete_one({"_id": oid})
        return ResponseHandler.delete_success(user.get("username"), str(user["_id"]), serialize_doc(user))

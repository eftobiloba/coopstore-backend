from fastapi import HTTPException, Depends, status
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from bson import ObjectId
from app.core.security import verify_password, get_user_token, get_token_payload, get_password_hash
from app.utils.responses import ResponseHandler
from app.schemas.auth import Signup


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthService:
    def __init__(self, db):
        self.users = db["user_collection"]

    async def login(self, user_credentials: OAuth2PasswordRequestForm):
        user = self.users.find_one({"username": user_credentials.username})  # No await
        print(user)
        if not user or not verify_password(user_credentials.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Credentials"
            )

        return await get_user_token(id=str(user["_id"]))

    def signup(self, user: Signup):
        hashed_password = get_password_hash(user.password)
        user_dict = user.model_dump()
        user_dict["password"] = hashed_password

        result = self.users.insert_one(user_dict)
        new_user = self.users.find_one({"_id": result.inserted_id})

        return ResponseHandler.create_success(new_user["username"], str(new_user["_id"]), new_user)

    async def get_refresh_token(self, token: str):
        payload = get_token_payload(token)
        user_id = payload.get("id", None)
        if not user_id:
            raise ResponseHandler.invalid_token("refresh")

        try:
            oid = ObjectId(user_id)
        except:
            raise ResponseHandler.invalid_token("refresh")

        user = self.users.find_one({"_id": oid})
        if not user:
            raise ResponseHandler.invalid_token("refresh")

        return await get_user_token(id=str(user["_id"]), refresh_token=token)

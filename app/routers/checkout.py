from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from app.schemas.carts import CheckoutBase
from app.db.database import carts_collection
from app.services.helpers import array_serialize_doc, serialize_doc

router = APIRouter(tags=["Checkout"], prefix="/checkout")

@router.post("/")
async def save_checkout(checkout: CheckoutBase):
    try:
        result = carts_collection.insert_one(checkout.dict())
        return {
            "message": "Checkout saved successfully",
            "checkout_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_all_checkouts():
    try:
        results = carts_collection.find()
        return {
            "message": "Checkouts found",
            "data": array_serialize_doc(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{id}")
async def get_one_checkout(id: str):
    try:
        checkout_id = ObjectId(id)
        results = carts_collection.find_one({"_id": checkout_id})
        results = serialize_doc(results)
        return {
            "message": f"Checkout with ID: {checkout_id} found",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
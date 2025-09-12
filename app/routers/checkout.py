from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pymongo import MongoClient
from bson import ObjectId
from app.schemas.carts import CheckoutBase
from app.db.database import carts_collection
from app.services.helpers import array_serialize_doc, serialize_doc
from app.services.notifications import send_email_via_api
from fastapi.encoders import jsonable_encoder

from app.utils.serializer import serialize_document

router = APIRouter(tags=["Checkout"], prefix="/checkout")

@router.post("/")
async def save_checkout(checkout: CheckoutBase, background_tasks: BackgroundTasks):
    try:
        checkout_request = checkout.dict()
        result = carts_collection.insert_one(checkout_request)

        checkout_request["_id"] = result.inserted_id
        serialized_checkout = serialize_document(checkout_request)  # ✅ safe dict

        background_tasks.add_task(
            send_email_via_api,
            "support@coopstoreonline.com",
            "An Order has been placed",
            "admin_order_pending.html",
            serialized_checkout
        )
        background_tasks.add_task(
            send_email_via_api,
            serialized_checkout["email"],
            "Your Order was placed successfully",
            "user_order_pending.html",
            serialized_checkout
        )

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
    
@router.delete("/{id}")
async def delete_checkout(id: str):
    try:
        checkout_id = ObjectId(id)
        result = carts_collection.delete_one({"_id": checkout_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Checkout with ID {id} not found")

        return {
            "message": f"Checkout with ID {id} deleted successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
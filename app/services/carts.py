from bson import ObjectId
from app.core.security import get_token_payload
from app.utils.responses import ResponseHandler
from app.schemas.carts import CartCreate, CartUpdate
from app.services.helpers import serialize_doc, array_serialize_doc


class CartService:
    def __init__(self, db):
        # db is your MongoDB database instance
        self.carts = db["carts_collection"]
        self.products = db["products_collection"]

    def get_all_carts(self, token, page: int, limit: int):
        print(token.credentials)
        user_id = get_token_payload(token.credentials).get("id")

        cursor = (
            self.carts.find({"user_id": user_id})
            .sort("_id", 1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        carts = array_serialize_doc(cursor)

        return ResponseHandler.success(f"Page {page} with {limit} carts", carts)

    def get_cart(self, token, cart_id: str):
        user_id = get_token_payload(token.credentials).get("id")
        try:
            oid = ObjectId(cart_id)
        except:
            return ResponseHandler.not_found_error("Cart", cart_id)

        cart = self.carts.find_one({"_id": oid, "user_id": user_id})
        if not cart:
            return ResponseHandler.not_found_error("Cart", cart_id)

        return ResponseHandler.get_single_success("cart", cart_id, serialize_doc(cart))

    def create_cart(self, token, cart: CartCreate):
        user_id = get_token_payload(token.credentials).get("id")
        cart_dict = cart.model_dump()
        cart_items_data = cart_dict.pop("cart_items", [])

        cart_items = []
        total_amount = 0

        for item in cart_items_data:
            product = self.products.find_one({"blob": item["product_id"]})
            if not product:
                return ResponseHandler.not_found_error("Product", item["product_id"])

            subtotal = item["quantity"] * product["price"] * (product["discount_percentage"] / 100)
            total_amount += subtotal
            cart_items.append({
                "product_id": str(item["product_id"]),
                "quantity": item["quantity"],
                "subtotal": subtotal
            })

        cart_doc = {
            "user_id": user_id,
            "cart_items": cart_items,
            "total_amount": total_amount,
            **cart_dict
        }
        result = self.carts.insert_one(cart_doc)
        new_cart = self.carts.find_one({"_id": result.inserted_id})

        return ResponseHandler.create_success("Cart", str(new_cart["_id"]), serialize_doc(new_cart))

    def update_cart(self, token, cart_id: str, updated_cart: CartUpdate):
        user_id = get_token_payload(token.credentials).get("id")
        try:
            cart_oid = ObjectId(cart_id)
        except:
            return ResponseHandler.not_found_error("Cart", cart_id)

        cart_exists = self.carts.find_one({"_id": cart_oid, "user_id": user_id})
        if not cart_exists:
            return ResponseHandler.not_found_error("Cart", cart_id)

        new_cart_items = []
        total_amount = 0

        for item in updated_cart.cart_items:
            try:
                prod_oid = ObjectId(item.product_id)
            except:
                return ResponseHandler.not_found_error("Product", item.product_id)

            product = self.products.find_one({"_id": prod_oid})
            if not product:
                return ResponseHandler.not_found_error("Product", item.product_id)

            subtotal = item.quantity * product["price"] * (product["discount_percentage"] / 100)
            total_amount += subtotal
            new_cart_items.append({
                "product_id": str(prod_oid),
                "quantity": item.quantity,
                "subtotal": subtotal
            })

        self.carts.update_one(
            {"_id": cart_oid, "user_id": user_id},
            {"$set": {"cart_items": new_cart_items, "total_amount": total_amount}}
        )

        updated = self.carts.find_one({"_id": cart_oid})
        return ResponseHandler.update_success("cart", cart_id, serialize_doc(updated))

    def delete_cart(self, token, cart_id: str):
        user_id = get_token_payload(token.credentials).get("id")
        try:
            cart_oid = ObjectId(cart_id)
        except:
            return ResponseHandler.not_found_error("Cart", cart_id)

        cart = self.carts.find_one({"_id": cart_oid, "user_id": user_id})
        if not cart:
            return ResponseHandler.not_found_error("Cart", cart_id)

        self.carts.delete_one({"_id": cart_oid, "user_id": user_id})
        return ResponseHandler.delete_success("Cart", cart_id, serialize_doc(cart))

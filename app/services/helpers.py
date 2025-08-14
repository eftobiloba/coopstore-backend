from bson import ObjectId

def serialize_doc(doc):
    return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}

def array_serialize_doc(cursor):
    return [serialize_doc(doc=doc) for doc in cursor]

def blob_generator(product):
    return "-".join(product.lower().split(" "))
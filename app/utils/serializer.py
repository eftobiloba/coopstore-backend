from datetime import datetime
from bson import ObjectId

def serialize_document(doc):
    """
    Recursively convert MongoDB documents (ObjectId, datetime, etc.)
    into JSON-serializable types.
    """
    if isinstance(doc, dict):
        return {k: serialize_document(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_document(v) for v in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    else:
        return doc

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_NAME = "sandmark-db"
COLLECTION_NAME = "sandmark-history"

_client = None
_collection = None


def get_collection():
    """Get MongoDB collection with lazy connection initialization."""
    global _client, _collection
    
    if _collection is not None:
        return _collection
    
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI is not set")
    
    try:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        # Test connection
        _client.admin.command('ping')
        
        db = _client[DATABASE_NAME]
        _collection = db[COLLECTION_NAME]
        return _collection
    
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")


def is_connected() -> bool:
    """Check if MongoDB is connected and available."""
    try:
        if _client is None:
            return False
        _client.admin.command('ping')
        return True
    except Exception:
        return False


def close_connection():
    """Close MongoDB connection."""
    global _client, _collection
    if _client is not None:
        _client.close()
        _client = None
        _collection = None

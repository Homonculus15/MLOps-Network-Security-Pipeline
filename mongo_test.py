from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_DB_URL")

client = MongoClient(uri, server_api=ServerApi("1"))

try:
    # Test connection
    client.admin.command("ping")
    print("1. Ping successful")

    # Test write
    db = client["NetworkSecurity"]
    collection = db["test_collection"]

    result = collection.insert_one({
        "test": "MongoDB write test"
    })

    print("2. Write successful")
    print("Inserted ID:", result.inserted_id)

except Exception as e:
    print("ERROR:", e)
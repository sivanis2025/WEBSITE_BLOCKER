from config.db import get_db

db = get_db()
db["blocked_sites"].delete_many({"site": {"$regex": "^e\.g\."}})
print("Cleaned!")

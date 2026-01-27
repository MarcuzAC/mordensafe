from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.client = MongoClient(mongodb_uri)
        self.db = self.client["fire_extinguisher_db"]
        print("✅ Connected to MongoDB")
    
    def get_collection(self, name):
        return self.db[name]

db = Database()

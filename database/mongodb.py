from motor.motor_asyncio import AsyncIOMotorClient
from config.setting import settings
import pymongo

print(settings.MONGODB_URI)
client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client['ProQuest']
users_collection = db['users']
resume_collection = db['resume']
user_responses = db['user_responses']
Company_collection = db['company']
interview_collection = db['interview']
user_company_collection = db['user_company']
Users_Test = db['users_test']
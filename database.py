
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def connection():
  client = MongoClient(os.getenv('MONGO_URI'))
  db = client.get_database(os.getenv('DB_NAME'))

  # Check DB connection
  try:
      client.admin.command('ping')
      print("Pinged your deployment. You successfully connected to MongoDB!")
  except Exception as e:
      print(e)

  return db
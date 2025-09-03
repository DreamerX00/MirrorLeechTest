#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load config.env file
load_dotenv("config.env", override=True)

# Get database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not DATABASE_URL or not BOT_TOKEN:
    print("DATABASE_URL or BOT_TOKEN not found!")
    exit(1)

bot_id = BOT_TOKEN.split(":", 1)[0]

print(f"Connecting to database for bot_id: {bot_id}")

# Connect to MongoDB
conn = MongoClient(DATABASE_URL)
db = conn.wzmlx

# Get current config from database
current_config = db.settings.config.find_one({"_id": bot_id}) or {}
if "_id" in current_config:
    del current_config["_id"]

print("Current AUTH_BOT settings in database:")
print(f"AUTH_BOT_ENABLED: {current_config.get('AUTH_BOT_ENABLED', 'Not set')}")
print(f"AUTH_BOT_TOKEN: {current_config.get('AUTH_BOT_TOKEN', 'Not set')[:20]}..." if current_config.get('AUTH_BOT_TOKEN') else "Not set")
print(f"AUTH_BOT_USERNAME: {current_config.get('AUTH_BOT_USERNAME', 'Not set')}")

# Update with AUTH_BOT settings from environment
auth_bot_config = {
    "AUTH_BOT_ENABLED": os.environ.get("AUTH_BOT_ENABLED", ""),
    "AUTH_BOT_TOKEN": os.environ.get("AUTH_BOT_TOKEN", ""),
    "AUTH_BOT_USERNAME": os.environ.get("AUTH_BOT_USERNAME", ""),
    "AUTH_BOT_TOKEN_SECRET": os.environ.get("AUTH_BOT_TOKEN_SECRET", "")
}

# Add to current config
current_config.update(auth_bot_config)

# Save back to database
db.settings.config.replace_one({"_id": bot_id}, current_config, upsert=True)

print("\nUpdated AUTH_BOT settings in database:")
print(f"AUTH_BOT_ENABLED: {auth_bot_config['AUTH_BOT_ENABLED']}")
print(f"AUTH_BOT_TOKEN: {auth_bot_config['AUTH_BOT_TOKEN'][:20]}..." if auth_bot_config['AUTH_BOT_TOKEN'] else "Not set")
print(f"AUTH_BOT_USERNAME: {auth_bot_config['AUTH_BOT_USERNAME']}")

conn.close()
print("Database updated successfully!")

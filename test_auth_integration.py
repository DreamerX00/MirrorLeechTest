#!/usr/bin/env python3
"""Test script to verify AUTH_BOT integration is working"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv("config.env", override=True)

# Test basic config loading
print("=== Basic Config Test ===")
print(f"BOT_TOKEN: {os.environ.get('BOT_TOKEN', 'Not set')[:20]}...")
print(f"DATABASE_URL: {'Set' if os.environ.get('DATABASE_URL') else 'Not set'}")

# Test AUTH_BOT config
print(f"\n=== AUTH_BOT Config Test ===")
auth_bot_enabled = os.environ.get("AUTH_BOT_ENABLED", "").lower() == "true"
print(f"AUTH_BOT_ENABLED: {auth_bot_enabled}")
print(f"AUTH_BOT_TOKEN: {os.environ.get('AUTH_BOT_TOKEN', 'Not set')[:20]}...")
print(f"AUTH_BOT_USERNAME: {os.environ.get('AUTH_BOT_USERNAME', 'Not set')}")

# Test database access
print(f"\n=== Database Test ===")
try:
    from pymongo import MongoClient
    DATABASE_URL = os.environ.get("DATABASE_URL")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    if DATABASE_URL and BOT_TOKEN:
        bot_id = BOT_TOKEN.split(":", 1)[0]
        conn = MongoClient(DATABASE_URL)
        db = conn.wzmlx
        
        config_from_db = db.settings.config.find_one({"_id": bot_id})
        if config_from_db:
            print(f"Database config found for bot_id: {bot_id}")
            print(f"AUTH_BOT_ENABLED in DB: {config_from_db.get('AUTH_BOT_ENABLED', 'Not set')}")
            print(f"AUTH_BOT_TOKEN in DB: {config_from_db.get('AUTH_BOT_TOKEN', 'Not set')[:20]}...")
            print(f"AUTH_BOT_USERNAME in DB: {config_from_db.get('AUTH_BOT_USERNAME', 'Not set')}")
        else:
            print("No database config found")
        conn.close()
    else:
        print("DATABASE_URL or BOT_TOKEN not available")
        
except Exception as e:
    print(f"Database test failed: {e}")

# Test if unauthorized_handler exists
print(f"\n=== Module Test ===")
try:
    import sys
    sys.path.append('/usr/src/app')
    
    # Test if files exist
    import os
    files_to_check = [
        "/usr/src/app/bot/modules/unauthorized_handler.py",
        "/usr/src/app/bot/helper/telegram_helper/filters.py",
        "/usr/src/app/bot/helper/ext_utils/bot_utils.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            
except Exception as e:
    print(f"Module test failed: {e}")

print(f"\n=== Summary ===")
if auth_bot_enabled:
    print("✓ AUTH_BOT integration is ENABLED")
    if os.environ.get('AUTH_BOT_TOKEN') and os.environ.get('AUTH_BOT_USERNAME'):
        print("✓ AUTH_BOT credentials are configured")
        print("✓ Ready for unauthorized user redirect functionality")
    else:
        print("✗ AUTH_BOT credentials missing")
else:
    print("✗ AUTH_BOT integration is DISABLED")

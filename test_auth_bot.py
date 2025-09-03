#!/usr/bin/env python3
"""Test auth_bot startup"""

import asyncio
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_auth_bot():
    """Test auth_bot initialization step by step"""
    
    print("=== Testing Auth Bot Startup ===")
    
    # Step 1: Test imports
    try:
        from auth_bot import AUTH_BOT_TOKEN, AUTH_BOT_USERNAME, TARGET_BOT_USERNAME
        print(f"✓ Configuration loaded successfully")
        print(f"  AUTH_BOT_TOKEN: {AUTH_BOT_TOKEN[:20]}..." if AUTH_BOT_TOKEN else "  AUTH_BOT_TOKEN: Not set")
        print(f"  AUTH_BOT_USERNAME: {AUTH_BOT_USERNAME}")
        print(f"  TARGET_BOT_USERNAME: {TARGET_BOT_USERNAME}")
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return
    
    # Step 2: Test database setup
    try:
        from auth_bot.setup_database import setup_database
        print("✓ Database setup module imported")
        
        db_setup = await setup_database()
        print(f"  Database setup result: {db_setup}")
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return
    
    # Step 3: Test Telegram application creation
    try:
        from telegram.ext import Application
        application = Application.builder().token(AUTH_BOT_TOKEN).build()
        print("✓ Telegram application created successfully")
    except Exception as e:
        print(f"✗ Telegram application failed: {e}")
        return
    
    # Step 4: Test command handlers
    try:
        from auth_bot.__main__ import start_command, help_command, subscription_command, verify_command
        from telegram.ext import CommandHandler
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        print("✓ Command handlers added successfully")
    except Exception as e:
        print(f"✗ Command handlers failed: {e}")
        return
    
    # Step 5: Test bot initialization (without starting polling)
    try:
        await application.initialize()
        print("✓ Bot initialized successfully")
        
        # Cleanup
        await application.shutdown()
        print("✓ Bot shutdown cleanly")
        
    except Exception as e:
        print(f"✗ Bot initialization failed: {e}")
        return
    
    print("=== All tests passed! Auth bot should work correctly ===")

if __name__ == "__main__":
    asyncio.run(test_auth_bot())

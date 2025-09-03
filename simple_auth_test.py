#!/usr/bin/env python3
"""Simple auth_bot test"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple test handler
async def simple_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple start command for testing"""
    user = update.effective_user
    await update.message.reply_text(f"Hello {user.first_name}! Simple test bot is working!")

async def simple_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple help command for testing"""
    await update.message.reply_text("This is a simple test bot to verify functionality.")

async def test_simple_bot():
    """Test a simple bot to see if Telegram connectivity works"""
    
    # Get token from auth_bot config
    from auth_bot import AUTH_BOT_TOKEN
    
    print(f"Starting simple test bot with token: {AUTH_BOT_TOKEN[:20]}...")
    
    # Create application
    application = Application.builder().token(AUTH_BOT_TOKEN).build()
    
    # Add simple handlers
    application.add_handler(CommandHandler("start", simple_start))
    application.add_handler(CommandHandler("help", simple_help))
    
    # Initialize and start
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Simple bot started! Try sending /start or /help")
    print("Press Ctrl+C to stop...")
    
    try:
        # Keep running for a reasonable time
        await asyncio.sleep(60)  # Run for 1 minute
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(test_simple_bot())

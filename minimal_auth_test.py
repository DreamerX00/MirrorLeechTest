#!/usr/bin/env python3
"""Minimal auth_bot test to identify the exact issue"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Simple test handlers
async def test_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple start command"""
    logger.info(f"START command received from user {update.effective_user.id}")
    try:
        await update.message.reply_text("✅ TEST START COMMAND WORKING!")
        logger.info("START response sent successfully")
    except Exception as e:
        logger.error(f"Error sending START response: {e}")

async def test_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple help command"""
    logger.info(f"HELP command received from user {update.effective_user.id}")
    try:
        await update.message.reply_text("✅ TEST HELP COMMAND WORKING!")
        logger.info("HELP response sent successfully")
    except Exception as e:
        logger.error(f"Error sending HELP response: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

async def main():
    """Run minimal test bot"""
    try:
        # Get token
        from auth_bot import AUTH_BOT_TOKEN
        logger.info(f"Using token: {AUTH_BOT_TOKEN[:20]}...")
        
        # Create application
        logger.info("Creating Telegram application...")
        application = Application.builder().token(AUTH_BOT_TOKEN).build()
        
        # Add handlers
        logger.info("Adding command handlers...")
        application.add_handler(CommandHandler("start", test_start))
        application.add_handler(CommandHandler("help", test_help))
        application.add_error_handler(error_handler)
        
        # Initialize and start
        logger.info("Initializing bot...")
        await application.initialize()
        
        logger.info("Starting bot...")
        await application.start()
        
        logger.info("Starting polling...")
        await application.updater.start_polling()
        
        logger.info("✅ Bot is now running and listening for messages!")
        logger.info("Send /start or /help to test")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            logger.info("Bot stopped")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

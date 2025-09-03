#!/usr/bin/env python3
# Auth Bot - run.py

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("auth_bot.log"),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Run the authorization bot"""
    try:
        # Import the main module
        from auth_bot.__main__ import main as bot_main
        
        # Run the bot
        await bot_main()
    except KeyboardInterrupt:
        logger.info("Authorization bot stopped by user")
    except Exception as e:
        logger.error(f"Error running authorization bot: {e}")
        raise


if __name__ == "__main__":
    try:
        # Run the main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Authorization bot stopped by user")
    except Exception as e:
        logger.error(f"Authorization bot crashed: {e}")
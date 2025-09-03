#!/usr/bin/env python3
# Auth Bot - Database Setup Script

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from auth_bot import DATABASE_URL

logger = logging.getLogger(__name__)

async def setup_database():
    """
    Automatically setup MongoDB database with required collections and indexes.
    """
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(DATABASE_URL)
        db = client.get_database()
        
        logger.info("Setting up auth_bot database...")
        
        # Create collections if they don't exist
        collections = ['users', 'subscriptions', 'payments', 'tokens']
        existing_collections = await db.list_collection_names()
        
        for collection_name in collections:
            if collection_name not in existing_collections:
                await db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
        
        # Create indexes for users collection
        await db.users.create_index("user_id", unique=True)
        await db.users.create_index("username")
        logger.info("Created indexes for users collection")
        
        # Create indexes for subscriptions collection
        await db.subscriptions.create_index("user_id", unique=True)
        await db.subscriptions.create_index("expiry_date")
        await db.subscriptions.create_index("is_active")
        logger.info("Created indexes for subscriptions collection")
        
        # Create indexes for payments collection
        await db.payments.create_index("user_id")
        await db.payments.create_index("payment_id", unique=True)
        await db.payments.create_index("status")
        await db.payments.create_index("created_at")
        logger.info("Created indexes for payments collection")
        
        # Create TTL index for tokens collection (6 hours expiry)
        await db.tokens.create_index("created_at", expireAfterSeconds=21600)
        await db.tokens.create_index("user_id")
        await db.tokens.create_index("token", unique=True)
        logger.info("Created indexes for tokens collection with TTL")
        
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(setup_database())

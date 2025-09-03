#!/usr/bin/env python3
# Auth Bot - Database Setup Script

import asyncio
import logging
import ssl
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from auth_bot import DATABASE_URL

logger = logging.getLogger(__name__)

async def test_connection_methods():
    """Test different connection methods to MongoDB"""
    # Use the original DATABASE_URL which already contains the database name
    
    connection_configs = [
        # Method 1: Standard connection
        {
            'name': 'Standard Connection',
            'config': {
                'serverSelectionTimeoutMS': 10000,
                'connectTimeoutMS': 10000,
                'socketTimeoutMS': 10000,
                'maxPoolSize': 10,
                'retryWrites': True
            }
        },
        # Method 2: With TLS options
        {
            'name': 'TLS Configured',
            'config': {
                'serverSelectionTimeoutMS': 10000,
                'connectTimeoutMS': 10000,
                'socketTimeoutMS': 10000,
                'maxPoolSize': 10,
                'retryWrites': True,
                'tls': True,
                'tlsCAFile': certifi.where(),
            }
        },
        # Method 3: Allow invalid certificates
        {
            'name': 'TLS Allow Invalid Certificates',
            'config': {
                'serverSelectionTimeoutMS': 10000,
                'connectTimeoutMS': 10000,
                'socketTimeoutMS': 10000,
                'maxPoolSize': 10,
                'retryWrites': True,
                'tls': True,
                'tlsAllowInvalidCertificates': True,
            }
        }
    ]
    
    for method in connection_configs:
        try:
            logger.info(f"Trying connection method: {method['name']}")
            client = AsyncIOMotorClient(DATABASE_URL, **method['config'])
            
            # Test the connection
            await client.admin.command('ping')
            logger.info(f"✅ Successfully connected using: {method['name']}")
            return client
            
        except Exception as e:
            logger.warning(f"❌ Connection method '{method['name']}' failed: {str(e)[:100]}...")
            try:
                client.close()
            except:
                pass
            continue
    
    return None

async def setup_database():
    """
    Automatically setup MongoDB database with required collections and indexes.
    """
    client = None
    try:
        logger.info(f"Setting up database connection to MongoDB Atlas...")
        
        # Try different connection methods
        client = await test_connection_methods()
        
        if not client:
            logger.error("❌ All connection methods failed!")
            return False
        
        # Get database - the database name is already specified in DATABASE_URL
        db = client.get_database()
        logger.info(f"Connected to MongoDB database: {db.name}")
        
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
        await db.subscriptions.create_index([("user_id", 1), ("created_at", -1)])
        await db.subscriptions.create_index("end_date")
        await db.subscriptions.create_index("status")
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
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(setup_database())

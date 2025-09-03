import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from auth_bot import (
    AUTO_REVOKE_EXPIRED, 
    FREE_TIER_FALLBACK, 
    FREE_TIER_COMMANDS,
    STANDARD_PLAN_DAYS
)
from auth_bot.database.db_handler import DBManager
from auth_bot.utils.notification import (
    send_expiry_notification, 
    send_subscription_expired_notification,
    send_subscription_activated_notification
)

logger = logging.getLogger(__name__)

# Initialize database
db = DBManager()

# Cache for active subscriptions to reduce database queries
subscription_cache = {}


async def get_subscription_status(user_id: int) -> Dict:
    """
    Get the subscription status for a user.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        Dictionary with subscription details
    """
    # Check cache first
    if user_id in subscription_cache and subscription_cache[user_id]["is_active"]:
        # Verify the cached subscription is not expired
        if subscription_cache[user_id]["expiry_date"] > datetime.now():
            return subscription_cache[user_id]
        else:
            # Remove expired subscription from cache
            del subscription_cache[user_id]
    
    # Get subscription from database
    subscription = await db.get_user_subscription(user_id)
    
    if not subscription:
        # Return default free tier subscription
        return {
            "user_id": user_id,
            "plan": "free",
            "is_active": True,
            "start_date": datetime.now(),
            "expiry_date": None,
            "commands": FREE_TIER_COMMANDS if FREE_TIER_COMMANDS else []
        }
    
    # Convert subscription object to dict
    subscription_dict = {
        "user_id": subscription.user_id,
        "plan": subscription.plan_type,
        "is_active": subscription.is_active,
        "start_date": subscription.start_date,
        "expiry_date": subscription.end_date,
        "commands": "*" if subscription.is_active else FREE_TIER_COMMANDS
    }
    
    # Check if subscription is expired
    if subscription_dict["expiry_date"] and subscription_dict["expiry_date"] < datetime.now():
        # Handle expired subscription
        await handle_expired_subscription(user_id, subscription_dict)
        
        # Get updated subscription after handling expiration
        subscription_dict = await get_subscription_status(user_id)
    
    # Cache active subscriptions
    if subscription_dict and subscription_dict["is_active"]:
        subscription_cache[user_id] = subscription_dict
    
    return subscription_dict


async def get_subscription(user_id: int) -> Optional[Dict]:
    """Get subscription from database (helper function)"""
    subscription = await db.get_user_subscription(user_id)
    if not subscription:
        return None
    
    return {
        "user_id": subscription.user_id,
        "plan": subscription.plan_type,
        "is_active": subscription.is_active,
        "start_date": subscription.start_date,
        "expiry_date": subscription.end_date,
        "commands": "*" if subscription.is_active else FREE_TIER_COMMANDS
    }


async def update_subscription(user_id: int, subscription_data: Dict) -> Dict:
    """Update subscription in database"""
    try:
        # Update subscription in database
        plan_days = (subscription_data["expiry_date"] - subscription_data["start_date"]).days
        success = await db.add_subscription(
            user_id=user_id,
            plan_type=subscription_data["plan"],
            plan_days=plan_days
        )
        
        if success:
            return subscription_data
        else:
            logger.error(f"Failed to update subscription for user {user_id}")
            return subscription_data
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        return subscription_data


async def revoke_subscription(user_id: int) -> bool:
    """Revoke a user's subscription"""
    try:
        success = await db.update_subscription(user_id, is_active=False)
        if success and user_id in subscription_cache:
            del subscription_cache[user_id]
        return success
    except Exception as e:
        logger.error(f"Error revoking subscription for user {user_id}: {e}")
        return False


async def update_user_subscription(user_id: int, plan_days: int) -> Dict:
    """
    Update a user's subscription with a new plan.
    
    Args:
        user_id: The Telegram user ID
        plan_days: Number of days for the subscription plan
        
    Returns:
        Updated subscription details
    """
    # Get current subscription
    current_subscription = await get_subscription(user_id)
    
    # Determine plan type based on days
    plan_type = "free"
    if plan_days == 7:
        plan_type = "basic"
    elif plan_days == 30:
        plan_type = "standard"
    elif plan_days == 90:
        plan_type = "premium"
    
    # Calculate new expiry date
    if current_subscription and current_subscription["is_active"] and current_subscription["expiry_date"]:
        # If subscription is active, extend from current expiry date
        if current_subscription["expiry_date"] > datetime.now():
            expiry_date = current_subscription["expiry_date"] + timedelta(days=plan_days)
        else:
            # If expired, start from now
            expiry_date = datetime.now() + timedelta(days=plan_days)
    else:
        # New subscription starts from now
        expiry_date = datetime.now() + timedelta(days=plan_days)
    
    # Create subscription data
    subscription_data = {
        "user_id": user_id,
        "plan": plan_type,
        "is_active": True,
        "start_date": datetime.now(),
        "expiry_date": expiry_date,
        "commands": "*"  # All commands allowed for paid plans
    }
    
    # Update subscription in database
    updated_subscription = await update_subscription(user_id, subscription_data)
    
    # Update cache
    subscription_cache[user_id] = updated_subscription
    
    # Send notification
    await send_subscription_activated_notification(user_id, plan_type, expiry_date)
    
    return updated_subscription


async def handle_expired_subscription(user_id: int, subscription: Dict) -> None:
    """
    Handle an expired subscription based on configuration settings.
    
    Args:
        user_id: The Telegram user ID
        subscription: The current subscription data
    """
    logger.info(f"Handling expired subscription for user {user_id}")
    
    if AUTO_REVOKE_EXPIRED:
        # Automatically revoke access
        await revoke_subscription(user_id)
        
        # Remove from cache if present
        if user_id in subscription_cache:
            del subscription_cache[user_id]
        
        if FREE_TIER_FALLBACK:
            # Create free tier subscription
            free_tier_data = {
                "user_id": user_id,
                "plan": "free",
                "is_active": True,
                "start_date": datetime.now(),
                "expiry_date": None,
                "commands": FREE_TIER_COMMANDS.split(",") if FREE_TIER_COMMANDS else []
            }
            
            # Update subscription in database
            await update_subscription(user_id, free_tier_data)
            
            # Update subscription status
            await db.update_subscription(user_id, is_active=False)
        else:
            # Update subscription status to inactive
            await db.update_subscription(user_id, is_active=False)
    
    # Send notification about expired subscription
    await send_subscription_expired_notification(user_id, subscription["plan"])


async def check_command_access(user_id: int, command: str) -> bool:
    """
    Check if a user has access to a specific command based on their subscription.
    
    Args:
        user_id: The Telegram user ID
        command: The command to check access for
        
    Returns:
        True if user has access, False otherwise
    """
    # Get subscription status
    subscription = await get_subscription_status(user_id)
    
    # Check if subscription is active
    if not subscription["is_active"]:
        return False
    
    # Check command access
    if subscription["commands"] == "*":
        # All commands allowed
        return True
    elif command in subscription["commands"]:
        # Specific command allowed
        return True
    
    return False


async def get_expiring_soon_subscriptions() -> List[Dict]:
    """
    Get a list of subscriptions that are expiring soon.
    
    Returns:
        List of subscription dictionaries
    """
    # Get subscriptions expiring in the next 7 days
    expiring_subscriptions = await get_expiring_subscriptions(7)
    
    return expiring_subscriptions


async def process_expired_subscriptions() -> List[int]:
    """
    Process all expired subscriptions and perform necessary actions.
    
    Returns:
        List of user IDs whose subscriptions were processed
    """
    logger.info("Processing expired subscriptions...")
    processed_users = []
    
    try:
        # Ensure database connection
        if not db._connected:
            await db.connect()
            
        # Get expired subscriptions from database
        expired_subscriptions = await db.get_expired_subscriptions()
        
        for subscription_data in expired_subscriptions:
            user_id = subscription_data["user_id"]
            
            # Handle expired subscription
            await handle_expired_subscription(user_id, subscription_data)
            processed_users.append(user_id)
            
            # Clear from cache
            if user_id in subscription_cache:
                del subscription_cache[user_id]
                
        logger.info(f"Processed {len(processed_users)} expired subscriptions")
        return processed_users
        
    except Exception as e:
        logger.error(f"Error processing expired subscriptions: {e}")
        return processed_users


async def get_expiring_subscriptions(days_ahead: int, include_expired: bool = False) -> List[Dict]:
    """Get subscriptions expiring within specified days"""
    try:
        # Ensure database connection
        if not db._connected:
            await db.connect()
            
        end_date = datetime.now() + timedelta(days=days_ahead)
        start_date = datetime.now() - timedelta(days=1) if include_expired else datetime.now()
        
        # Query database for subscriptions expiring soon
        pipeline = [
            {
                "$match": {
                    "end_date": {"$gte": start_date, "$lte": end_date},
                    "status": "active"
                }
            }
        ]
        
        cursor = db.db.subscriptions.aggregate(pipeline)
        return await cursor.to_list(length=None)
    except Exception as e:
        logger.error(f"Error getting expiring subscriptions: {e}")
        return []


async def get_user(user_id: int) -> Optional[Dict]:
    """Get user information from database"""
    try:
        user = await db.get_user(user_id)
        return user.__dict__ if user else None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


async def get_renewal_options(user_id: int) -> List[Dict]:
    """
    Get available renewal options for a user.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        List of available renewal plans
    """
    user = await get_user(user_id)
    
    if not user:
        return []
    
    # Standard renewal options
    renewal_options = [
        {"plan": "basic", "days": 7, "price": 5.0},
        {"plan": "standard", "days": 30, "price": 15.0},
        {"plan": "premium", "days": 90, "price": 40.0}
    ]
    
    return renewal_options
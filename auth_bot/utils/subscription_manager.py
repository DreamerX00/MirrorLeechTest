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
    subscription = await get_subscription(user_id)
    
    if not subscription:
        # Return default free tier subscription
        return {
            "user_id": user_id,
            "plan": "free",
            "is_active": True,
            "start_date": datetime.now(),
            "expiry_date": None,
            "commands": FREE_TIER_COMMANDS.split(",") if FREE_TIER_COMMANDS else []
        }
    
    # Check if subscription is expired
    if subscription["expiry_date"] and subscription["expiry_date"] < datetime.now():
        # Handle expired subscription
        await handle_expired_subscription(user_id, subscription)
        
        # Get updated subscription after handling expiration
        subscription = await get_subscription(user_id)
    
    # Cache active subscriptions
    if subscription and subscription["is_active"]:
        subscription_cache[user_id] = subscription
    
    return subscription


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
            
            # Update user status
            await update_user(user_id, {"subscription_status": "free"})
        else:
            # Update user status to inactive
            await update_user(user_id, {"subscription_status": "inactive"})
    
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


async def process_expired_subscriptions() -> int:
    """
    Process all expired subscriptions.
    
    Returns:
        Number of processed subscriptions
    """
    # Get expired subscriptions
    expired_subscriptions = await get_expiring_subscriptions(0, include_expired=True)
    
    count = 0
    for subscription in expired_subscriptions:
        if subscription["expiry_date"] < datetime.now() and subscription["is_active"]:
            # Handle expired subscription
            await handle_expired_subscription(subscription["user_id"], subscription)
            count += 1
    
    return count


async def get_renewal_options(user_id: int) -> Dict:
    """
    Get subscription renewal options for a user.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        Dictionary with renewal options
    """
    # Get current subscription
    subscription = await get_subscription_status(user_id)
    
    # Get user details
    user = await get_user(user_id)
    
    options = {
        "current_plan": subscription["plan"],
        "expiry_date": subscription["expiry_date"],
        "is_active": subscription["is_active"],
        "can_renew": True,
        "recommended_plan": "standard",  # Default recommendation
        "has_payment_method": bool(user.get("payment_method")),
        "available_plans": ["basic", "standard", "premium"],
        "free_tier_available": bool(FREE_TIER_FALLBACK)
    }
    
    # Customize recommendation based on usage patterns
    if user.get("usage_count", 0) > 100:
        options["recommended_plan"] = "premium"
    elif user.get("usage_count", 0) < 20:
        options["recommended_plan"] = "basic"
    
    return options
#!/usr/bin/env python3
# Auth Bot - handlers/subscription.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union

from auth_bot import (
    BASIC_PLAN_DAYS, STANDARD_PLAN_DAYS, PREMIUM_PLAN_DAYS,
    BASIC_PLAN_PRICE, STANDARD_PLAN_PRICE, PREMIUM_PLAN_PRICE,
    NOTIFICATION_ENABLED, subscription_data
)
from auth_bot.database.db_handler import DBManager

logger = logging.getLogger(__name__)

# Initialize database
db = DBManager()

async def get_subscription_status(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a user's subscription status.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        The subscription data as a dictionary, or None if no subscription exists
    """
    try:
        # Check if subscription data is cached
        if user_id in subscription_data:
            # Check if cached data is still valid
            cached_subscription = subscription_data[user_id]
            if cached_subscription.get("expiry_date") > datetime.now() and cached_subscription.get("is_active"):
                return cached_subscription
        
        # Get subscription from database
        subscription = await db.get_subscription(user_id)
        
        # Cache subscription data if it exists and is active
        if subscription and subscription.get("is_active"):
            subscription_data[user_id] = subscription
        elif user_id in subscription_data:
            # Remove from cache if subscription is not active
            del subscription_data[user_id]
        
        return subscription
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        return None

async def update_subscription(user_id: int, plan_days: int) -> bool:
    """
    Update a user's subscription.
    
    Args:
        user_id: The Telegram user ID
        plan_days: Number of days for the subscription
        
    Returns:
        True if the update was successful, False otherwise
    """
    try:
        # Determine plan name based on days
        if plan_days == BASIC_PLAN_DAYS:
            plan_name = "Basic"
        elif plan_days == STANDARD_PLAN_DAYS:
            plan_name = "Standard"
        elif plan_days == PREMIUM_PLAN_DAYS:
            plan_name = "Premium"
        else:
            plan_name = "Custom"
        
        # Get current subscription
        current_subscription = await db.get_subscription(user_id)
        
        if current_subscription and current_subscription.get("is_active"):
            # Extend existing subscription
            success = await db.extend_subscription(user_id, plan_days)
            
            # Update cached subscription data
            if success:
                updated_subscription = await db.get_subscription(user_id)
                if updated_subscription:
                    subscription_data[user_id] = updated_subscription
        else:
            # Add new subscription
            success = await db.add_subscription(user_id, plan_days, plan_name)
            
            # Cache new subscription data
            if success:
                new_subscription = await db.get_subscription(user_id)
                if new_subscription:
                    subscription_data[user_id] = new_subscription
        
        return success
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        return False

async def revoke_subscription(user_id: int) -> bool:
    """
    Revoke a user's subscription.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        True if the revocation was successful, False otherwise
    """
    try:
        # Update subscription to inactive
        success = await db.update_subscription(user_id, is_active=False)
        
        # Remove from cache if successful
        if success and user_id in subscription_data:
            del subscription_data[user_id]
        
        return success
    except Exception as e:
        logger.error(f"Error revoking subscription: {e}")
        return False

async def check_subscription_expiry(user_id: int) -> bool:
    """
    Check if a user's subscription has expired.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        True if the subscription is active, False if it has expired or doesn't exist
    """
    try:
        subscription = await get_subscription_status(user_id)
        
        if not subscription:
            return False
        
        return subscription.get("is_active", False)
    except Exception as e:
        logger.error(f"Error checking subscription expiry: {e}")
        return False

async def get_plan_details(plan_type: str) -> Dict[str, Union[str, int, float]]:
    """
    Get details for a subscription plan.
    
    Args:
        plan_type: The plan type (basic, standard, premium)
        
    Returns:
        A dictionary containing plan details
    """
    plan_type = plan_type.lower()
    
    if plan_type == "basic":
        return {
            "name": "Basic",
            "days": BASIC_PLAN_DAYS,
            "price": BASIC_PLAN_PRICE
        }
    elif plan_type == "standard":
        return {
            "name": "Standard",
            "days": STANDARD_PLAN_DAYS,
            "price": STANDARD_PLAN_PRICE
        }
    elif plan_type == "premium":
        return {
            "name": "Premium",
            "days": PREMIUM_PLAN_DAYS,
            "price": PREMIUM_PLAN_PRICE
        }
    else:
        # Default to basic plan
        return {
            "name": "Basic",
            "days": BASIC_PLAN_DAYS,
            "price": BASIC_PLAN_PRICE
        }

async def get_expiring_subscriptions(days: int = 1) -> list:
    """
    Get subscriptions that are about to expire within the specified number of days.
    
    Args:
        days: Number of days to check for expiration
        
    Returns:
        A list of subscription data dictionaries that are about to expire
    """
    try:
        return await db.get_expiring_subscriptions(days)
    except Exception as e:
        logger.error(f"Error getting expiring subscriptions: {e}")
        return []

async def send_expiry_notifications(bot) -> None:
    """
    Send notifications to users whose subscriptions are about to expire.
    
    Args:
        bot: The Telegram bot instance
    """
    if not NOTIFICATION_ENABLED:
        return
    
    try:
        # Get subscriptions expiring in 1 day
        expiring_soon = await get_expiring_subscriptions(1)
        
        for subscription in expiring_soon:
            user_id = subscription.get("user_id")
            expiry_date = subscription.get("expiry_date")
            
            if user_id and expiry_date:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"⚠️ *Subscription Expiry Notice*\n\n"
                             f"Your subscription will expire in less than 24 hours on {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
                             f"To continue using the service, please renew your subscription.",
                        parse_mode="Markdown"
                    )
                    logger.info(f"Sent expiry notification to user {user_id}")
                except Exception as e:
                    logger.error(f"Error sending expiry notification to user {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in send_expiry_notifications: {e}")
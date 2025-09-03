import logging
from typing import Optional, Dict, Tuple

from auth_bot import FREE_TIER_COMMANDS, AUTO_REVOKE_EXPIRED
from auth_bot.utils.subscription_manager import get_subscription_status, check_command_access
from auth_bot.utils.token_generator import verify_access_token

logger = logging.getLogger(__name__)


async def check_user_authorization(user_id: int, command: str) -> bool:
    """
    Check if a user is authorized to use a specific command.
    
    Args:
        user_id: The Telegram user ID
        command: The command to check authorization for
        
    Returns:
        True if authorized, False otherwise
    """
    # Check if command is allowed for all users (free tier)
    if command in FREE_TIER_COMMANDS.split(","):
        return True
    
    # Check subscription-based access
    return await check_command_access(user_id, command)


async def verify_user_token(token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Verify a user's access token.
    
    Args:
        token: The access token to verify
        
    Returns:
        Tuple of (is_valid, token_data)
    """
    is_valid, token_data = await verify_access_token(token)
    
    if not is_valid:
        logger.warning(f"Invalid access token: {token[:10]}...")
        return False, None
    
    # Check if user has an active subscription
    user_id = token_data.get("user_id")
    if not user_id:
        logger.warning(f"Token missing user_id: {token[:10]}...")
        return False, None
    
    subscription = await get_subscription_status(user_id)
    
    # If auto-revoke is enabled and subscription is not active, token is invalid
    if AUTO_REVOKE_EXPIRED and not subscription["is_active"]:
        logger.warning(f"User {user_id} has inactive subscription, token invalidated")
        return False, None
    
    return True, token_data


async def get_user_permissions(user_id: int) -> Dict:
    """
    Get the permissions for a user based on their subscription.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        Dictionary with permission details
    """
    subscription = await get_subscription_status(user_id)
    
    permissions = {
        "is_active": subscription["is_active"],
        "plan": subscription["plan"],
        "expiry_date": subscription["expiry_date"],
        "allowed_commands": subscription["commands"] if subscription["is_active"] else [],
        "can_download": subscription["is_active"] and subscription["plan"] != "free",
        "can_leech": subscription["is_active"] and subscription["plan"] in ["standard", "premium"],
        "can_clone": subscription["is_active"] and subscription["plan"] in ["standard", "premium"],
        "max_concurrent_tasks": 1 if subscription["plan"] == "free" else 
                                3 if subscription["plan"] == "basic" else 
                                5 if subscription["plan"] == "standard" else 10
    }
    
    return permissions
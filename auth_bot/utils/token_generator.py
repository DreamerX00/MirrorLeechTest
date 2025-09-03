import logging
import secrets
import string
import base64
import json
import time
import uuid
import hmac
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet

from auth_bot import TOKEN_EXPIRY_HOURS, TOKEN_SECRET_KEY
from auth_bot.database.db_handler import DBManager
from auth_bot.utils.notification import send_token_notification

logger = logging.getLogger(__name__)

# Initialize database
db = DBManager()

# Initialize encryption key
try:
    encryption_key = Fernet(base64.urlsafe_b64encode(TOKEN_SECRET_KEY[:32].ljust(32, '0').encode()))
except Exception as e:
    logger.error(f"Failed to initialize encryption key: {e}")
    encryption_key = None


async def get_token_by_value(token: str) -> Optional[Dict]:
    """Get token data from database by token value"""
    return await db.get_token(token)


async def invalidate_token(token: str) -> bool:
    """Mark token as used in database"""
    return await db.use_token(token)


async def get_user(user_id: int) -> Optional[Dict]:
    """Get user data from database"""
    user = await db.get_user(user_id)
    return user.__dict__ if user else None


async def update_user(user_id: int, update_data: Dict) -> bool:
    """Update user data in database"""
    try:
        await db.update_user_activity(user_id)
        return True
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False


async def generate_token(user_id: int, plan_days: int = 0) -> str:
    """
    Generate a secure token for user authorization.
    
    Args:
        user_id: The Telegram user ID
        plan_days: Number of days for the subscription plan (0 for free tier)
        
    Returns:
        A secure token string
    """
    try:
        # Create token data
        token_data = {
            "user_id": user_id,
            "plan_days": plan_days,
            "created_at": int(time.time()),
            "expires_at": int(time.time() + TOKEN_EXPIRY_HOURS * 3600),
            "uuid": str(uuid.uuid4())
        }
        
        # Convert token data to JSON string
        token_json = json.dumps(token_data)
        
        # Encode token data
        encoded_data = base64.urlsafe_b64encode(token_json.encode()).decode()
        
        # Generate HMAC signature
        signature = hmac.new(
            TOKEN_SECRET_KEY.encode(),
            encoded_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine encoded data and signature
        token = f"{encoded_data}.{signature}"
        
        # Store token in database
        await db.add_token(token, user_id, datetime.fromtimestamp(token_data["expires_at"]))
        
        logger.info(f"Generated token for user {user_id} with {plan_days} days")
        return token
        
    except Exception as e:
        logger.error(f"Error generating token for user {user_id}: {e}")
        raise


async def validate_token(token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate a token and return user information if valid.
    
    Args:
        token: The token to validate
        
    Returns:
        Tuple of (is_valid, token_data)
    """
    # Get token from database
    token_data = await get_token_by_value(token)
    
    if not token_data:
        logger.warning(f"Token not found: {token}")
        return False, None
    
    # Check if token is expired
    if datetime.now() > token_data["expires_at"]:
        logger.warning(f"Token expired: {token}")
        return False, None
    
    # Check if token is already used
    if token_data["is_used"]:
        logger.warning(f"Token already used: {token}")
        return False, None
    
    # Mark token as used
    await invalidate_token(token)
    
    return True, token_data


async def generate_access_token(user_id: int, subscription_days: int) -> str:
    """
    Generate a JWT access token for the user with subscription information.
    
    Args:
        user_id: The Telegram user ID
        subscription_days: Number of days for the subscription
        
    Returns:
        JWT token string
    """
    # Get user information
    user = await get_user(user_id)
    
    if not user:
        logger.error(f"User not found: {user_id}")
        return ""
    
    # Create JWT payload
    payload = {
        "user_id": user_id,
        "username": user.get("username", ""),
        "subscription_days": subscription_days,
        "exp": int(time.time() + (subscription_days * 24 * 60 * 60)),
        "iat": int(time.time())
    }
    
    try:
        # Generate JWT token
        jwt_token = jwt.encode(payload, TOKEN_SECRET_KEY, algorithm="HS256")
        
        # Encrypt the token for additional security if encryption is available
        if encryption_key:
            encrypted_token = encryption_key.encrypt(jwt_token.encode()).decode()
            await update_user(user_id, {"access_token": encrypted_token})
            return encrypted_token
        else:
            await update_user(user_id, {"access_token": jwt_token})
            return jwt_token
    except Exception as e:
        logger.error(f"Error generating access token: {e}")
        return ""


async def verify_access_token(token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Verify a JWT access token (encrypted or plain).
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Tuple of (is_valid, token_data)
    """
    try:
        jwt_token = token
        
        # Try to decrypt if encryption is available
        if encryption_key:
            try:
                jwt_token = encryption_key.decrypt(token.encode()).decode()
            except Exception:
                # If decryption fails, assume it's a plain JWT
                pass
        
        # Verify and decode JWT token
        payload = jwt.decode(jwt_token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        
        # Check if token is expired
        if "exp" in payload and int(time.time()) > payload["exp"]:
            logger.warning(f"Access token expired for user {payload.get('user_id')}")
            return False, None
        
        return True, payload
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {e}")
        return False, None
    except jwt.ExpiredSignatureError as e:
        logger.error(f"Expired JWT token: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Error verifying access token: {e}")
        return False, None


async def generate_verification_url(user_id: int, plan_days: int = 0) -> str:
    """
    Generate a verification URL with an embedded token.
    
    Args:
        user_id: The Telegram user ID
        plan_days: Number of days for the subscription plan (0 for free tier)
        
    Returns:
        The verification URL (shortened if available, otherwise original)
    """
    from auth_bot import TARGET_BOT_USERNAME
    from auth_bot.utils.url_shortener import shorten_url
    
    try:
        # Generate token
        token = await generate_token(user_id, plan_days)
        
        # Create verification URL
        verification_url = f"https://t.me/{TARGET_BOT_USERNAME}?start=verify_{token}"
        
        # Try to shorten URL if shortener is available
        try:
            shortened_url = await shorten_url(verification_url)
            # Return shortened URL if successful and different from original
            if shortened_url and shortened_url != verification_url:
                logger.info(f"URL shortened successfully for user {user_id}")
                return shortened_url
            else:
                logger.info(f"URL shortener not available or failed, using original URL for user {user_id}")
                return verification_url
        except Exception as e:
            logger.warning(f"URL shortening failed for user {user_id}: {e}, using original URL")
            return verification_url
            
    except Exception as e:
        logger.error(f"Error generating verification URL for user {user_id}: {e}")
        raise
#!/usr/bin/env python3
# Auth Bot - utils/token_manager.py

import uuid
import json
import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional, Any, Union

from auth_bot import TOKEN_SECRET_KEY, TOKEN_TIMEOUT_HOURS

def generate_token(user_id: int, plan_days: int) -> str:
    """
    Generate a secure token for user authorization.
    
    Args:
        user_id: The Telegram user ID
        plan_days: Number of days for the subscription plan
        
    Returns:
        A secure token string
    """
    # Create token data
    token_data = {
        "user_id": user_id,
        "plan_days": plan_days,
        "created_at": int(time.time()),
        "expires_at": int(time.time() + TOKEN_TIMEOUT_HOURS * 3600),
        "uuid": str(uuid.uuid4())
    }
    
    # Convert token data to JSON string
    token_json = json.dumps(token_data)
    
    # Encode token data
    encoded_data = base64.urlsafe_b64encode(token_json.encode()).decode()
    
    # Generate HMAC signature
    signature = generate_signature(encoded_data)
    
    # Combine encoded data and signature
    token = f"{encoded_data}.{signature}"
    
    return token

def validate_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate a token and extract its data.
    
    Args:
        token: The token to validate
        
    Returns:
        A tuple containing (is_valid, token_data)
        If the token is invalid, token_data will be None
    """
    try:
        # Split token into data and signature
        parts = token.split('.')
        if len(parts) != 2:
            return False, None
        
        encoded_data, signature = parts
        
        # Verify signature
        expected_signature = generate_signature(encoded_data)
        if not hmac.compare_digest(signature, expected_signature):
            return False, None
        
        # Decode token data
        token_json = base64.urlsafe_b64decode(encoded_data).decode()
        token_data = json.loads(token_json)
        
        # Check if token has expired
        current_time = int(time.time())
        if token_data.get("expires_at", 0) < current_time:
            return False, None
        
        return True, token_data
    except Exception as e:
        print(f"Token validation error: {e}")
        return False, None

def generate_signature(data: str) -> str:
    """
    Generate an HMAC signature for the given data.
    
    Args:
        data: The data to sign
        
    Returns:
        The HMAC signature as a hex string
    """
    key = TOKEN_SECRET_KEY.encode()
    message = data.encode()
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return signature

def encrypt_user_data(user_id: int) -> str:
    """
    Encrypt user data for secure storage or transmission.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        Encrypted user data string
    """
    # Create user data
    user_data = {
        "user_id": user_id,
        "timestamp": int(time.time())
    }
    
    # Convert to JSON string
    user_json = json.dumps(user_data)
    
    # Encode user data
    encoded_data = base64.urlsafe_b64encode(user_json.encode()).decode()
    
    # Generate signature
    signature = generate_signature(encoded_data)
    
    # Combine encoded data and signature
    encrypted_data = f"{encoded_data}.{signature}"
    
    return encrypted_data

def decrypt_user_data(encrypted_data: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Decrypt and validate user data.
    
    Args:
        encrypted_data: The encrypted user data string
        
    Returns:
        A tuple containing (is_valid, user_data)
        If the data is invalid, user_data will be None
    """
    try:
        # Split data into encoded data and signature
        parts = encrypted_data.split('.')
        if len(parts) != 2:
            return False, None
        
        encoded_data, signature = parts
        
        # Verify signature
        expected_signature = generate_signature(encoded_data)
        if not hmac.compare_digest(signature, expected_signature):
            return False, None
        
        # Decode user data
        user_json = base64.urlsafe_b64decode(encoded_data).decode()
        user_data = json.loads(user_json)
        
        return True, user_data
    except Exception as e:
        print(f"User data decryption error: {e}")
        return False, None

def is_token_expired(token_time: int) -> bool:
    """
    Check if a token has expired based on its creation time.
    
    Args:
        token_time: The token creation timestamp
        
    Returns:
        True if the token has expired, False otherwise
    """
    current_time = int(time.time())
    expiry_time = token_time + (TOKEN_TIMEOUT_HOURS * 3600)
    return current_time > expiry_time

def get_token_expiry_date(token_time: int) -> datetime:
    """
    Get the expiry date for a token.
    
    Args:
        token_time: The token creation timestamp
        
    Returns:
        The expiry date as a datetime object
    """
    expiry_timestamp = token_time + (TOKEN_TIMEOUT_HOURS * 3600)
    return datetime.fromtimestamp(expiry_timestamp)

def get_subscription_expiry_date(start_time: int, plan_days: int) -> datetime:
    """
    Calculate the expiry date for a subscription.
    
    Args:
        start_time: The subscription start timestamp
        plan_days: Number of days for the subscription
        
    Returns:
        The expiry date as a datetime object
    """
    start_date = datetime.fromtimestamp(start_time)
    expiry_date = start_date + timedelta(days=plan_days)
    return expiry_date
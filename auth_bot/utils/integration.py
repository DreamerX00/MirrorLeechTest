#!/usr/bin/env python3
# Auth Bot - utils/integration.py

import logging
from datetime import datetime
from typing import Dict, Optional, Any, Union, Tuple

from auth_bot import TARGET_BOT_USERNAME, AUTH_BOT_USERNAME
from auth_bot.utils.token_manager import generate_token, validate_token
from auth_bot.utils.url_shortener import shorten_url
from auth_bot.handlers.subscription import check_subscription_expiry

logger = logging.getLogger(__name__)

async def check_user_authorization(user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Check if a user is authorized to use the target bot.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        A tuple containing (is_authorized, verification_message)
        If the user is authorized, verification_message will be None
    """
    try:
        # Check if user has an active subscription
        is_authorized = await check_subscription_expiry(user_id)
        
        if is_authorized:
            return True, None
        
        # Generate a temporary token for verification
        token = generate_token(user_id, 0)  # 0 days means temporary token
        
        # Create verification link
        verification_link = f"https://t.me/{AUTH_BOT_USERNAME}?start={token}"
        
        # Shorten the verification link
        short_link = await shorten_url(verification_link)
        verification_link = short_link if short_link else verification_link
        
        # Create verification message
        verification_message = (
            f"⚠️ You are not authorized to use {TARGET_BOT_USERNAME}.\n\n"
            f"Please verify your access by clicking the link below:\n"
            f"{verification_link}\n\n"
            f"This verification link will expire in 6 hours."
        )
        
        return False, verification_message
    except Exception as e:
        logger.error(f"Error checking user authorization: {e}")
        return False, "An error occurred while checking your authorization. Please try again later."

async def intercept_command(user_id: int, command: str) -> Tuple[bool, Optional[str]]:
    """
    Intercept a command from the target bot and check if the user is authorized.
    
    Args:
        user_id: The Telegram user ID
        command: The command being executed
        
    Returns:
        A tuple containing (should_proceed, message)
        If should_proceed is True, the command should be allowed to execute
        If should_proceed is False, the message should be sent to the user
    """
    try:
        # Check if the command requires authorization
        if not requires_authorization(command):
            return True, None
        
        # Check if the user is authorized
        is_authorized, verification_message = await check_user_authorization(user_id)
        
        if is_authorized:
            return True, None
        else:
            return False, verification_message
    except Exception as e:
        logger.error(f"Error intercepting command: {e}")
        return True, None  # Allow the command to proceed in case of error

def requires_authorization(command: str) -> bool:
    """
    Check if a command requires authorization.
    
    Args:
        command: The command being executed
        
    Returns:
        True if the command requires authorization, False otherwise
    """
    # List of commands that require authorization
    restricted_commands = [
        "mirror", "leech", "clone", "count", "download", "upload",
        "ytdl", "ytdlzip", "qbmirror", "qbleech", "qbunzip", "qbzip",
        "rss", "search", "status", "cancel", "cancelall", "exec",
        "restart", "stats", "usage", "user", "scrape", "myfilesset",
        "storage", "cleanup", "delete", "config", "category", "mirror_status",
        "leech_status", "speedtest", "shell", "log", "ping", "restart",
        "update", "authorize", "unauthorize", "users", "addleechlog",
        "rmleechlog", "leechlogs", "setthumb", "rmthumb", "rmsthumb",
        "addleechlog", "rmleechlog", "leechlogs", "setthumb", "rmthumb",
        "rmsthumb", "thumbnails", "mediainfo", "speedtest", "log", "ping",
        "restart", "update", "authorize", "unauthorize", "users", "auth",
        "unauth", "addsudo", "rmsudo", "blacklist", "rmblacklist", "bl",
        "rmbl", "rmtdcache", "gdtot", "jiodrive", "shortener", "setdump",
        "rmdump", "setdumpid", "rmdumpid", "dumps", "addrss", "rmrss",
        "listrss", "pauserss", "resumerss", "rssmonitor", "rsssettings",
        "rssget", "rsssub", "rssunsub", "rssunsuball", "rsslist", "rssctl",
        "rsssettings", "rssget", "rsssub", "rssunsub", "rssunsuball", "rsslist",
        "rssctl", "filter", "filters", "rmfilter", "rmfilters", "filterlist",
        "setfilterthumb", "rmfilterthumb", "filterthumb", "filterlist",
        "setfilterthumb", "rmfilterthumb", "filterthumb", "botpm", "usertd",
        "setname", "setusername", "setbio", "setpic", "setdesc", "setprefix",
        "setsuffix", "setremname", "setcaption", "setvid", "setaudio",
        "setdump", "rmdump", "setdumpid", "rmdumpid", "dumps", "addrss",
        "rmrss", "listrss", "pauserss", "resumerss", "rssmonitor", "rsssettings",
        "rssget", "rsssub", "rssunsub", "rssunsuball", "rsslist", "rssctl"
    ]
    
    # Check if the command is in the restricted list
    command = command.lower().split('@')[0].strip('/')
    return command in restricted_commands

async def validate_verification_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate a verification token.
    
    Args:
        token: The token to validate
        
    Returns:
        A tuple containing (is_valid, token_data)
        If the token is invalid, token_data will be None
    """
    return validate_token(token)
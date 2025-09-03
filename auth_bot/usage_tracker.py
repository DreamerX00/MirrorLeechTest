#!/usr/bin/env python3
# Auth Bot - Usage Tracking Integration

import logging
import time
from datetime import datetime
from functools import wraps
from typing import Callable, Any

from auth_bot.database.db_handler import DBManager

logger = logging.getLogger(__name__)

class UsageTracker:
    def __init__(self):
        self.db = DBManager()
    
    def track_command(self, command_name: str):
        """Decorator to track command usage"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                user_id = None
                success = True
                error_message = None
                
                try:
                    # Extract user_id from update object
                    if args and hasattr(args[0], 'effective_user'):
                        user_id = args[0].effective_user.id
                    
                    # Execute the original function
                    result = await func(*args, **kwargs)
                    
                    return result
                    
                except Exception as e:
                    success = False
                    error_message = str(e)
                    logger.error(f"Error in {command_name}: {e}")
                    raise
                    
                finally:
                    # Log usage statistics
                    if user_id:
                        response_time = time.time() - start_time
                        await self.db.log_command_usage(
                            user_id=user_id,
                            command=command_name,
                            success=success,
                            response_time=response_time,
                            error_message=error_message
                        )
            
            return wrapper
        return decorator

# Global usage tracker instance
usage_tracker = UsageTracker()

# Convenience decorators for common commands
def track_start_command(func):
    return usage_tracker.track_command("start")(func)

def track_help_command(func):
    return usage_tracker.track_command("help")(func)

def track_subscription_command(func):
    return usage_tracker.track_command("subscription")(func)

def track_verify_command(func):
    return usage_tracker.track_command("verify")(func)

def track_admin_command(func):
    return usage_tracker.track_command("admin")(func)

def track_payment_callback(func):
    return usage_tracker.track_command("payment_callback")(func)

def track_plan_selection(func):
    return usage_tracker.track_command("plan_selection")(func)

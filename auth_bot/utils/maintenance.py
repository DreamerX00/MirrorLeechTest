import asyncio
import logging
from datetime import datetime, timedelta

from auth_bot import NOTIFICATION_ENABLED
from auth_bot.utils.subscription_manager import process_expired_subscriptions, get_expiring_soon_subscriptions
from auth_bot.utils.notification import send_expiry_notification

logger = logging.getLogger(__name__)


async def maintenance_task() -> None:
    """
    Periodic maintenance task to process expired subscriptions and send notifications.
    """
    while True:
        try:
            # Process expired subscriptions
            processed_count = await process_expired_subscriptions()
            if processed_count > 0:
                logger.info(f"Processed {processed_count} expired subscriptions")
            
            # Send notifications for expiring subscriptions if enabled
            if NOTIFICATION_ENABLED:
                expiring_subscriptions = await get_expiring_soon_subscriptions()
                for subscription in expiring_subscriptions:
                    days_left = (subscription["expiry_date"] - datetime.now()).days
                    
                    # Send notifications at 7, 3, and 1 days before expiry
                    if days_left in [7, 3, 1]:
                        await send_expiry_notification(
                            subscription["user_id"],
                            subscription["plan"],
                            subscription["expiry_date"],
                            days_left
                        )
            
            # Wait for next run (every hour)
            await asyncio.sleep(3600)  # 1 hour
        except Exception as e:
            logger.error(f"Error in maintenance task: {e}")
            await asyncio.sleep(300)  # 5 minutes retry on error


async def setup_maintenance_scheduler() -> None:
    """
    Set up the maintenance scheduler.
    """
    # Start maintenance task
    asyncio.create_task(maintenance_task())
    logger.info("Maintenance scheduler started")
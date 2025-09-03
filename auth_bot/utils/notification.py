# Auth Bot - utils/notification.py

import logging
from datetime import datetime, timedelta
import asyncio

from telegram import Bot
from telegram.error import TelegramError

from auth_bot import NOTIFICATION_ENABLED, AUTH_BOT_TOKEN
from auth_bot.database.db_handler import DBManager

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages notifications for subscription expiry and other events"""
    
    def __init__(self, bot=None):
        """Initialize the notification manager
        
        Args:
            bot: Telegram Bot instance
        """
        self.bot = bot or Bot(AUTH_BOT_TOKEN)
        self.db = DBManager()
        self.notification_enabled = NOTIFICATION_ENABLED
    
    async def send_expiry_notification(self, user_id, days_left):
        """Send a notification about subscription expiry
        
        Args:
            user_id: Telegram user ID
            days_left: Number of days left before expiry
        
        Returns:
            bool: True if notification was sent, False otherwise
        """
        if not self.notification_enabled:
            return False
        
        try:
            message = f"⚠️ *Subscription Expiry Notice* ⚠️\n\n"
            
            if days_left > 0:
                message += f"Your subscription will expire in *{days_left} days*. "
                message += "Please renew your subscription to continue using the bot."
            else:
                message += "Your subscription has *expired*. "
                message += "Please renew your subscription to continue using the bot."
            
            message += "\n\nUse /subscription to view available plans."
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Update notification status in database
            await self.db.update_notification_status(user_id, datetime.now())
            
            return True
        
        except TelegramError as e:
            logger.error(f"Failed to send expiry notification to {user_id}: {e}")
            return False
    
    async def send_subscription_activated(self, user_id, plan_name, expiry_date):
        """Send a notification about subscription activation
        
        Args:
            user_id: Telegram user ID
            plan_name: Name of the subscription plan
            expiry_date: Expiry date of the subscription
        
        Returns:
            bool: True if notification was sent, False otherwise
        """
        try:
            expiry_str = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
            
            message = f"✅ *Subscription Activated* ✅\n\n"
            message += f"Your *{plan_name}* subscription has been activated.\n"
            message += f"Expiry Date: *{expiry_str}*\n\n"
            message += "Thank you for subscribing!"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
        
        except TelegramError as e:
            logger.error(f"Failed to send activation notification to {user_id}: {e}")
            return False
    
    async def send_admin_notification(self, message):
        """Send a notification to all admin users
        
        Args:
            message: Message to send
        
        Returns:
            bool: True if notification was sent to at least one admin, False otherwise
        """
        from auth_bot import ADMIN_USER_IDS
        
        success = False
        
        for admin_id in ADMIN_USER_IDS:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
                success = True
            except TelegramError as e:
                logger.error(f"Failed to send admin notification to {admin_id}: {e}")
        
        return success
    
    async def check_expiring_subscriptions(self):
        """Check for expiring subscriptions and send notifications
        
        This method should be called periodically to check for subscriptions
        that are about to expire and send notifications to users.
        """
        if not self.notification_enabled:
            return
        
        # Get all active subscriptions
        subscriptions = await self.db.get_all_active_subscriptions()
        
        now = datetime.now()
        
        for subscription in subscriptions:
            user_id = subscription['user_id']
            expiry_date = subscription['expiry_date']
            last_notified = subscription.get('last_notified')
            
            # Calculate days left
            days_left = (expiry_date - now).days
            
            # Send notification if subscription is about to expire
            # Notify at 7 days, 3 days, 1 day before expiry, and on expiry day
            if days_left in [7, 3, 1, 0]:
                # Check if notification was already sent today
                if last_notified and (now - last_notified).days < 1:
                    continue
                
                await self.send_expiry_notification(user_id, days_left)
    
    async def start_notification_scheduler(self):
        """Start the notification scheduler
        
        This method starts a background task that periodically checks for
        expiring subscriptions and sends notifications.
        """
        if not self.notification_enabled:
            logger.info("Notification scheduler is disabled")
            return
        
        logger.info("Starting notification scheduler")
        
        while True:
            try:
                await self.check_expiring_subscriptions()
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")
            
            # Run once a day
            await asyncio.sleep(24 * 60 * 60)


async def send_token_notification(user_id, token, plan_name):
    """Send token notification to user
    
    Args:
        user_id: Telegram user ID
        token: Generated access token
        plan_name: Subscription plan name
    
    Returns:
        bool: True if notification was sent, False otherwise
    """
    try:
        bot = Bot(AUTH_BOT_TOKEN)
        message = f"🎉 *Token Generated* 🎉\n\n"
        message += f"Plan: *{plan_name}*\n"
        message += f"Token: `{token}`\n\n"
        message += "Use this token to access the main bot!"
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send token notification: {e}")
        return False
#!/usr/bin/env python3
# Auth Bot - Webhook Handler for Payment Automation

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from telegram import Bot
from auth_bot import (
    AUTH_BOT_TOKEN, BASIC_PLAN_DAYS, STANDARD_PLAN_DAYS, PREMIUM_PLAN_DAYS,
    NOTIFICATION_ENABLED
)
from auth_bot.database.db_handler import DBManager
from auth_bot.utils.subscription_manager import update_user_subscription
from auth_bot.utils.notification import send_subscription_activated_notification

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self):
        self.db = DBManager()
        self.bot = Bot(token=AUTH_BOT_TOKEN)

    async def handle_stripe_webhook(self, payload: Dict[str, Any]) -> bool:
        """Handle Stripe webhook for automatic payment processing"""
        try:
            event_type = payload.get('type')
            
            if event_type == 'checkout.session.completed':
                session = payload['data']['object']
                payment_id = session['metadata'].get('payment_id')
                user_id = int(session['metadata'].get('user_id'))
                plan_type = session['metadata'].get('plan_type')
                plan_days = int(session['metadata'].get('plan_days'))
                
                # Update payment status
                await self.db.update_payment_status(payment_id, 'completed')
                
                # Activate subscription automatically
                await update_user_subscription(user_id, plan_days)
                
                # Send confirmation to user
                await self.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ *Payment Successful!*\n\n"
                         f"Your {plan_type.title()} plan has been activated.\n"
                         f"Duration: {plan_days} days\n"
                         f"Expiry: {(datetime.now() + timedelta(days=plan_days)).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                         f"You now have full access to the bot!",
                    parse_mode='Markdown'
                )
                
                logger.info(f"Automatically activated subscription for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {e}")
            return False

    async def handle_paypal_webhook(self, payload: Dict[str, Any]) -> bool:
        """Handle PayPal webhook for automatic payment processing"""
        try:
            event_type = payload.get('event_type')
            
            if event_type == 'PAYMENT.SALE.COMPLETED':
                payment = payload['resource']
                payment_id = payment['custom']  # We store our payment_id in custom field
                
                # Get payment details from database
                payment_record = await self.db.get_payment(payment_id)
                if not payment_record:
                    logger.error(f"Payment record not found: {payment_id}")
                    return False
                
                user_id = payment_record['user_id']
                plan_days = payment_record['plan_days']
                plan_type = payment_record['plan_type']
                
                # Update payment status
                await self.db.update_payment_status(payment_id, 'completed')
                
                # Activate subscription automatically
                await update_user_subscription(user_id, plan_days)
                
                # Send confirmation to user
                await self.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ *Payment Successful!*\n\n"
                         f"Your {plan_type.title()} plan has been activated.\n"
                         f"Duration: {plan_days} days\n"
                         f"Expiry: {(datetime.now() + timedelta(days=plan_days)).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                         f"You now have full access to the bot!",
                    parse_mode='Markdown'
                )
                
                logger.info(f"Automatically activated subscription for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {e}")
            return False

    async def handle_upi_confirmation(self, payment_id: str, transaction_id: str) -> bool:
        """Handle UPI payment confirmation (manual or via payment gateway)"""
        try:
            # Get payment details from database
            payment_record = await self.db.get_payment(payment_id)
            if not payment_record:
                logger.error(f"Payment record not found: {payment_id}")
                return False
            
            user_id = payment_record['user_id']
            plan_days = payment_record['plan_days']
            plan_type = payment_record['plan_type']
            
            # Update payment status with transaction ID
            await self.db.update_payment_status(payment_id, 'completed', transaction_id)
            
            # Activate subscription automatically
            await update_user_subscription(user_id, plan_days)
            
            # Send confirmation to user
            await self.bot.send_message(
                chat_id=user_id,
                text=f"✅ *UPI Payment Successful!*\n\n"
                     f"Transaction ID: `{transaction_id}`\n"
                     f"Your {plan_type.title()} plan has been activated.\n"
                     f"Duration: {plan_days} days\n"
                     f"Expiry: {(datetime.now() + timedelta(days=plan_days)).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                     f"You now have full access to the bot!",
                parse_mode='Markdown'
            )
            
            logger.info(f"Automatically activated UPI subscription for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing UPI confirmation: {e}")
            return False

# Global webhook handler instance
webhook_handler = WebhookHandler()

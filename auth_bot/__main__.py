#!/usr/bin/env python3
# Auth Bot - __main__.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import asyncio

from . import (
    AUTH_BOT_TOKEN, AUTH_BOT_USERNAME, TARGET_BOT_USERNAME, ADMIN_USER_IDS, OWNER_ID,
    BASIC_PLAN_DAYS, STANDARD_PLAN_DAYS, PREMIUM_PLAN_DAYS,
    BASIC_PLAN_PRICE, STANDARD_PLAN_PRICE, PREMIUM_PLAN_PRICE,
    AUTO_REVOKE_EXPIRED, FREE_TIER_FALLBACK, NOTIFICATION_ENABLED
)
from .utils.token_generator import generate_token, validate_token, generate_verification_url
from .utils.url_shortener import shorten_url
from .database.db_handler import DBManager
from .handlers.subscription import get_subscription_status
from .utils.subscription_manager import update_user_subscription, process_expired_subscriptions, get_renewal_options
from .payment.payment_handler import process_payment, generate_payment_link
from .utils.notification import setup_notification_scheduler, send_subscription_activated_notification
from .handlers.verify import verify_command, handle_verify_callback
from .utils.maintenance import setup_maintenance_scheduler
from .setup_database import setup_database
from .usage_tracker import track_start_command, track_help_command, track_subscription_command, track_verify_command, track_admin_command, track_payment_callback
from .analytics_dashboard import start_analytics_server
from .webhook_server import start_webhook_server

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = DBManager()

# Admin user IDs are already parsed in __init__.py as a list
admin_ids = ADMIN_USER_IDS

# Command handlers
@track_start_command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Start command received from user {user_id}")
    
    # Simple database check with error handling
    try:
        if not await db.user_exists(user_id):
            await db.add_user(user_id, user.username, user.first_name)
            logger.info(f"New user added: {user_id}")
    except Exception as e:
        logger.warning(f"Database operation failed for user {user_id}: {e}")
        # Continue without database - this is not critical for basic functionality
    
    # Check if start command contains a token (deep linking)
    if context.args and len(context.args) > 0:
        token = context.args[0]
        if token.startswith("verify_"):
            token = token.replace("verify_", "")
        
        # Validate token
        try:
            is_valid, token_data = await validate_token(token)
            if is_valid and token_data:
                # Update user subscription based on token plan
                plan_days = token_data.get("plan_days", 0)
                if plan_days > 0:
                    try:
                        await update_user_subscription(user_id, plan_days)
                        await update.message.reply_text(
                            f"✅ Your subscription has been activated successfully!\n\n"
                            f"Plan: {plan_days} days\n"
                            f"You now have full access to {TARGET_BOT_USERNAME}."
                        )
                    except Exception as e:
                        logger.error(f"Subscription update failed: {e}")
                        await update.message.reply_text(
                            f"✅ Your verification was successful!\n\n"
                            f"You now have access to {TARGET_BOT_USERNAME}."
                        )
                else:
                    # Free tier verification
                    await update.message.reply_text(
                        f"✅ Your verification was successful!\n\n"
                        f"You now have basic access to {TARGET_BOT_USERNAME}."
                    )
                return
            else:
                await update.message.reply_text(
                    "❌ Invalid or expired verification token.\n\n"
                    "Please request a new verification link."
                )
                return
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            await update.message.reply_text(
                "❌ Error processing your token. Please try again."
            )
            return
    
    # Simple welcome message - generate access link via button to avoid startup issues
    keyboard = [
        [InlineKeyboardButton("🚀 Get Free Access", callback_data="generate_free_access")],
        [InlineKeyboardButton(f"🔹 Basic Plan ({BASIC_PLAN_DAYS} days) - ${BASIC_PLAN_PRICE}", callback_data=f"plan_basic")],
        [InlineKeyboardButton(f"🔸 Standard Plan ({STANDARD_PLAN_DAYS} days) - ${STANDARD_PLAN_PRICE}", callback_data=f"plan_standard")],
        [InlineKeyboardButton(f"💎 Premium Plan ({PREMIUM_PLAN_DAYS} days) - ${PREMIUM_PLAN_PRICE}", callback_data=f"plan_premium")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="my_subscription")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎉 Welcome to {TARGET_BOT_USERNAME} Authorization!\n\n"
        f"Get instant FREE access to {TARGET_BOT_USERNAME} or choose a premium plan.\n\n"
        f"📱 *Free Access:* Click below for immediate access\n"
        f"💎 *Premium Plans:* Enhanced features and unlimited access\n\n"
        f"Choose an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

@track_help_command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        f"🔹 *{AUTH_BOT_USERNAME} Help*\n\n"
        f"This bot manages access to {TARGET_BOT_USERNAME} through subscription plans.\n\n"
        f"*Available Commands:*\n"
        f"/start - Start the bot and view subscription plans\n"
        f"/help - Show this help message\n"
        f"/subscription - Check your current subscription status\n"
        f"/verify - Generate a verification link for your subscription\n\n"
        f"*Subscription Plans:*\n"
        f"• Basic: {BASIC_PLAN_DAYS} days - ${BASIC_PLAN_PRICE}\n"
        f"• Standard: {STANDARD_PLAN_DAYS} days - ${STANDARD_PLAN_PRICE}\n"
        f"• Premium: {PREMIUM_PLAN_DAYS} days - ${PREMIUM_PLAN_PRICE}\n\n"
        f"For any issues, please contact an admin."
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

@track_subscription_command
async def subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check user's subscription status."""
    user_id = update.effective_user.id
    subscription = await get_subscription_status(user_id)
    
    if subscription and subscription['is_active']:
        expiry_date = subscription['expiry_date']
        days_left = (expiry_date - datetime.now()).days
        
        await update.message.reply_text(
            f"📊 *Your Subscription*\n\n"
            f"Status: ✅ Active\n"
            f"Plan: {subscription['plan_name']}\n"
            f"Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Days Left: {days_left}\n\n"
            f"You can use {TARGET_BOT_USERNAME} until your subscription expires.",
            parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton(f"🔹 Basic Plan ({BASIC_PLAN_DAYS} days) - ${BASIC_PLAN_PRICE}", callback_data=f"plan_basic")],
            [InlineKeyboardButton(f"🔸 Standard Plan ({STANDARD_PLAN_DAYS} days) - ${STANDARD_PLAN_PRICE}", callback_data=f"plan_standard")],
            [InlineKeyboardButton(f"💎 Premium Plan ({PREMIUM_PLAN_DAYS} days) - ${PREMIUM_PLAN_PRICE}", callback_data=f"plan_premium")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ You don't have an active subscription.\n\n"
            f"Please select a subscription plan to continue:",
            reply_markup=reply_markup
        )

@track_verify_command
async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify a token provided by the user."""
    user_id = update.effective_user.id
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "Please provide a token to verify.\n\n"
            "Example: /verify YOUR_TOKEN_HERE"
        )
        return
    
    token = context.args[0]
    is_valid, token_data = await validate_token(token)
    
    if is_valid:
        # Update user subscription
        await update_user_subscription(user_id, token_data['plan_days'])
        await update.message.reply_text(
            f"✅ Token verified successfully!\n\n"
            f"You now have access to {TARGET_BOT_USERNAME} for {token_data['plan_days']} days.\n\n"
            f"Expiry date: {(datetime.now() + timedelta(days=token_data['plan_days'])).strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        await update.message.reply_text("❌ Invalid or expired token. Please purchase a subscription.")

# Admin commands
@track_admin_command
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel for managing users and subscriptions."""
    user_id = update.effective_user.id
    
    if user_id not in admin_ids:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 List Users", callback_data="admin_list_users")],
        [InlineKeyboardButton("🎟️ Generate Token", callback_data="admin_generate_token")],
        [InlineKeyboardButton("🔄 Update User Subscription", callback_data="admin_update_subscription")],
        [InlineKeyboardButton("❌ Revoke Subscription", callback_data="admin_revoke_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Admin Panel*\n\n"
        "Select an action:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    callback_data = query.data
    
    # Handle verification callbacks
    if callback_data == "generate_link":
        await handle_verify_callback(update, context)
        return
    
    if callback_data == "generate_free_access":
        # Generate free access token for any user
        try:
            logger.info(f"Generating free access for user {user_id}")
            verification_url = await generate_verification_url(user_id, 0)  # 0 = free tier
            
            keyboard = [
                [InlineKeyboardButton("🚀 Access Main Bot", url=verification_url)],
                [InlineKeyboardButton("🔄 Generate New Link", callback_data="generate_free_access")],
                [InlineKeyboardButton("💎 Upgrade to Premium", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🎉 *Free Access Generated!*\n\n"
                f"Your verification link is ready! Click the button below to access {TARGET_BOT_USERNAME}.\n\n"
                f"🔗 This link will expire in 6 hours\n"
                f"🆓 Free tier includes basic features\n"
                f"💎 Upgrade to premium for unlimited access",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            logger.info(f"Free access link generated successfully for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error generating free access for user {user_id}: {e}")
            await query.edit_message_text(
                f"❌ Sorry, there was an error generating your access link.\n\n"
                f"This might be a temporary issue. Please try again in a moment.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data="generate_free_access")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
                ])
            )
        return
    
    if callback_data == "help":
        help_text = (
            f"🔹 *{AUTH_BOT_USERNAME} Help*\n\n"
            f"This bot manages access to {TARGET_BOT_USERNAME} through subscription plans.\n\n"
            f"*Available Commands:*\n"
            f"/start - Start the bot and view subscription plans\n"
            f"/help - Show this help message\n"
            f"/subscription - Check your current subscription status\n"
            f"/verify - Verify your token (if you have one)\n\n"
            f"*Subscription Plans:*\n"
            f"• Basic: {BASIC_PLAN_DAYS} days - ${BASIC_PLAN_PRICE}\n"
            f"• Standard: {STANDARD_PLAN_DAYS} days - ${STANDARD_PLAN_PRICE}\n"
            f"• Premium: {PREMIUM_PLAN_DAYS} days - ${PREMIUM_PLAN_PRICE}\n\n"
            f"For any issues, please contact an admin."
        )
        await query.edit_message_text(text=help_text, parse_mode='Markdown')
    
    elif callback_data == "show_plans":
        keyboard = [
            [InlineKeyboardButton("🆓 Get Free Access", callback_data="generate_free_access")],
            [InlineKeyboardButton(f"🔹 Basic Plan ({BASIC_PLAN_DAYS} days) - ${BASIC_PLAN_PRICE}", callback_data=f"plan_basic")],
            [InlineKeyboardButton(f"🔸 Standard Plan ({STANDARD_PLAN_DAYS} days) - ${STANDARD_PLAN_PRICE}", callback_data=f"plan_standard")],
            [InlineKeyboardButton(f"💎 Premium Plan ({PREMIUM_PLAN_DAYS} days) - ${PREMIUM_PLAN_PRICE}", callback_data=f"plan_premium")],
            [InlineKeyboardButton("📊 My Subscription", callback_data="my_subscription")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎯 *Choose Your Access Level*\n\n"
            f"🆓 **Free Access:** Basic features, limited usage\n"
            f"🔹 **Basic Plan:** {BASIC_PLAN_DAYS} days - ${BASIC_PLAN_PRICE}\n"
            f"🔸 **Standard Plan:** {STANDARD_PLAN_DAYS} days - ${STANDARD_PLAN_PRICE}\n"
            f"💎 **Premium Plan:** {PREMIUM_PLAN_DAYS} days - ${PREMIUM_PLAN_PRICE}\n\n"
            f"Select an option below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "my_subscription":
        subscription = await get_subscription_status(user_id)
        
        if subscription and subscription['is_active']:
            expiry_date = subscription['expiry_date']
            days_left = (expiry_date - datetime.now()).days
            
            await query.edit_message_text(
                f"📊 *Your Subscription*\n\n"
                f"Status: ✅ Active\n"
                f"Plan: {subscription['plan_name']}\n"
                f"Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Days Left: {days_left}\n\n"
                f"You can use {TARGET_BOT_USERNAME} until your subscription expires.",
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton(f"🔹 Basic Plan ({BASIC_PLAN_DAYS} days) - ${BASIC_PLAN_PRICE}", callback_data=f"plan_basic")],
                [InlineKeyboardButton(f"🔸 Standard Plan ({STANDARD_PLAN_DAYS} days) - ${STANDARD_PLAN_PRICE}", callback_data=f"plan_standard")],
                [InlineKeyboardButton(f"💎 Premium Plan ({PREMIUM_PLAN_DAYS} days) - ${PREMIUM_PLAN_PRICE}", callback_data=f"plan_premium")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ You don't have an active subscription.\n\n"
                f"Please select a subscription plan to continue:",
                reply_markup=reply_markup
            )
    
    elif callback_data.startswith("plan_"):
        plan_type = callback_data.split("_")[1]
        
        if plan_type == "basic":
            plan_days = BASIC_PLAN_DAYS
            plan_price = BASIC_PLAN_PRICE
            plan_name = "Basic"
        elif plan_type == "standard":
            plan_days = STANDARD_PLAN_DAYS
            plan_price = STANDARD_PLAN_PRICE
            plan_name = "Standard"
        elif plan_type == "premium":
            plan_days = PREMIUM_PLAN_DAYS
            plan_price = PREMIUM_PLAN_PRICE
            plan_name = "Premium"
        
        # Show payment method selection
        keyboard = [
            [InlineKeyboardButton("💳 Credit/Debit Card", callback_data=f"pay_{plan_type}_card")],
            [InlineKeyboardButton("📱 UPI Payment", callback_data=f"pay_{plan_type}_upi")],
            [InlineKeyboardButton("🏦 Net Banking", callback_data=f"pay_{plan_type}_netbanking")],
            [InlineKeyboardButton("💰 PayPal", callback_data=f"pay_{plan_type}_paypal")],
            [InlineKeyboardButton("🏧 Bank Transfer", callback_data=f"pay_{plan_type}_bank")],
            [InlineKeyboardButton("₿ Cryptocurrency", callback_data=f"pay_{plan_type}_crypto")],
            [InlineKeyboardButton("💵 Manual Payment", callback_data=f"pay_{plan_type}_manual")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💰 *{plan_name} Plan Selected*\n\n"
            f"• Duration: {plan_days} days\n"
            f"• Price: ${plan_price}\n\n"
            f"Choose your preferred payment method:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("pay_"):
        # Handle payment method selection
        parts = callback_data.split("_")
        plan_type = parts[1]
        payment_method = parts[2]
        
        if plan_type == "basic":
            plan_days = BASIC_PLAN_DAYS
            plan_price = BASIC_PLAN_PRICE
            plan_name = "Basic"
        elif plan_type == "standard":
            plan_days = STANDARD_PLAN_DAYS
            plan_price = STANDARD_PLAN_PRICE
            plan_name = "Standard"
        elif plan_type == "premium":
            plan_days = PREMIUM_PLAN_DAYS
            plan_price = PREMIUM_PLAN_PRICE
            plan_name = "Premium"
        
        # Generate payment link based on method
        payment_link = await generate_payment_link(user_id, plan_type, plan_days, plan_price, payment_method)
        
        # Shorten the payment link if URL shortener is configured
        if payment_link:
            short_link = await shorten_url(payment_link)
            # If shortening fails or is not configured, use original link
            payment_link = short_link if short_link and short_link != payment_link else payment_link
        
        # Payment method display names
        method_names = {
            "card": "💳 Credit/Debit Card",
            "upi": "📱 UPI Payment", 
            "netbanking": "🏦 Net Banking",
            "paypal": "💰 PayPal",
            "bank": "🏧 Bank Transfer",
            "crypto": "₿ Cryptocurrency",
            "manual": "💵 Manual Payment"
        }
        
        keyboard = [
            [InlineKeyboardButton("💳 Pay Now", url=payment_link)],
            [InlineKeyboardButton("🔙 Back to Plans", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💳 *Payment Details*\n\n"
            f"Plan: {plan_name} ({plan_days} days)\n"
            f"Amount: ${plan_price}\n"
            f"Method: {method_names.get(payment_method, payment_method.title())}\n\n"
            f"Click 'Pay Now' to complete your payment. Your subscription will be activated automatically after successful payment.\n\n"
            f"💡 *Note:* Keep this chat open to receive payment confirmation.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton(f"🔹 Basic Plan ({BASIC_PLAN_DAYS} days) - ${BASIC_PLAN_PRICE}", callback_data=f"plan_basic")],
            [InlineKeyboardButton(f"🔸 Standard Plan ({STANDARD_PLAN_DAYS} days) - ${STANDARD_PLAN_PRICE}", callback_data=f"plan_standard")],
            [InlineKeyboardButton(f"💎 Premium Plan ({PREMIUM_PLAN_DAYS} days) - ${PREMIUM_PLAN_PRICE}", callback_data=f"plan_premium")],
            [InlineKeyboardButton("📊 My Subscription", callback_data="my_subscription")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Welcome to the {TARGET_BOT_USERNAME} Authorization Bot!\n\n"
            f"This bot helps you get access to {TARGET_BOT_USERNAME} through our subscription plans.\n\n"
            f"Please select a subscription plan to continue:",
            reply_markup=reply_markup
        )
    
    # Admin callbacks
    elif callback_data.startswith("admin_") and user_id in admin_ids:
        admin_action = callback_data.split("_")[1]
        
        if admin_action == "list_users":
            users = await db.get_all_users()
            user_list = "👥 *User List*\n\n"
            
            for user in users[:10]:  # Limit to 10 users to avoid message too long
                subscription = await get_subscription_status(user['user_id'])
                status = "✅ Active" if subscription and subscription['is_active'] else "❌ Inactive"
                user_list += f"ID: {user['user_id']}\nUsername: @{user['username'] or 'N/A'}\nName: {user['first_name']}\nStatus: {status}\n\n"
            
            await query.edit_message_text(user_list, parse_mode='Markdown')
        
        elif admin_action == "generate_token":
            # Store the admin action in user_data for the next step
            context.user_data['admin_action'] = 'generate_token'
            
            await query.edit_message_text(
                "🎟️ *Generate Token*\n\n"
                "Please send the plan type (basic, standard, premium) followed by the user ID.\n\n"
                "Example: `basic 123456789`",
                parse_mode='Markdown'
            )
        
        elif admin_action == "update_subscription":
            # Store the admin action in user_data for the next step
            context.user_data['admin_action'] = 'update_subscription'
            
            await query.edit_message_text(
                "🔄 *Update User Subscription*\n\n"
                "Please send the user ID followed by the plan type (basic, standard, premium).\n\n"
                "Example: `123456789 premium`",
                parse_mode='Markdown'
            )
        
        elif admin_action == "revoke_subscription":
            # Store the admin action in user_data for the next step
            context.user_data['admin_action'] = 'revoke_subscription'
            
            await query.edit_message_text(
                "❌ *Revoke Subscription*\n\n"
                "Please send the user ID to revoke their subscription.\n\n"
                "Example: `123456789`",
                parse_mode='Markdown'
            )

# Admin action handler
async def admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin actions that require text input."""
    user_id = update.effective_user.id
    
    if user_id not in admin_ids:
        return
    
    if 'admin_action' not in context.user_data:
        return
    
    admin_action = context.user_data['admin_action']
    message_text = update.message.text
    
    if admin_action == 'generate_token':
        try:
            parts = message_text.split()
            plan_type = parts[0].lower()
            target_user_id = int(parts[1])
            
            if plan_type == "basic":
                plan_days = BASIC_PLAN_DAYS
            elif plan_type == "standard":
                plan_days = STANDARD_PLAN_DAYS
            elif plan_type == "premium":
                plan_days = PREMIUM_PLAN_DAYS
            else:
                await update.message.reply_text("❌ Invalid plan type. Use basic, standard, or premium.")
                return
            
            # Generate token
            token = generate_token(target_user_id, plan_days)
            
            # Create verification link
            verification_link = f"https://t.me/{AUTH_BOT_USERNAME}?start={token}"
            
            # Shorten the link if URL shortener is configured
            short_link = await shorten_url(verification_link)
            verification_link = short_link if short_link and short_link != verification_link else verification_link
            
            await update.message.reply_text(
                f"🎟️ *Token Generated Successfully*\n\n"
                f"Plan: {plan_type.capitalize()}\n"
                f"Duration: {plan_days} days\n"
                f"User ID: {target_user_id}\n\n"
                f"Token: `{token}`\n\n"
                f"Verification Link:\n{verification_link}",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid format. Use: plan_type user_id")
    
    elif admin_action == 'update_subscription':
        try:
            parts = message_text.split()
            target_user_id = int(parts[0])
            plan_type = parts[1].lower()
            
            if plan_type == "basic":
                plan_days = BASIC_PLAN_DAYS
            elif plan_type == "standard":
                plan_days = STANDARD_PLAN_DAYS
            elif plan_type == "premium":
                plan_days = PREMIUM_PLAN_DAYS
            else:
                await update.message.reply_text("❌ Invalid plan type. Use basic, standard, or premium.")
                return
            
            # Update user subscription
            await update_user_subscription(target_user_id, plan_days)
            
            await update.message.reply_text(
                f"✅ *Subscription Updated Successfully*\n\n"
                f"User ID: {target_user_id}\n"
                f"Plan: {plan_type.capitalize()}\n"
                f"Duration: {plan_days} days\n"
                f"Expiry Date: {(datetime.now() + timedelta(days=plan_days)).strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode='Markdown'
            )
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid format. Use: user_id plan_type")
    
    elif admin_action == 'revoke_subscription':
        try:
            target_user_id = int(message_text.strip())
            
            # Revoke user subscription
            await db.update_subscription(target_user_id, is_active=False)
            
            await update.message.reply_text(
                f"❌ *Subscription Revoked Successfully*\n\n"
                f"User ID: {target_user_id}",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID.")
    
    # Clear the admin action
    del context.user_data['admin_action']

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        # Send message to the user
        await update.effective_message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )
    except:
        pass

async def main() -> None:
    """Start the bot."""
    # Setup database automatically
    db_setup_success = await setup_database()
    if not db_setup_success:
        logger.error("Failed to setup database. Exiting...")
        return
    
    # Connect the global database manager
    try:
        await db.connect()
        logger.info("Database manager connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect database manager: {e}")
        logger.info("Bot will continue with limited functionality")
    
    # Create the Application
    application = Application.builder().token(AUTH_BOT_TOKEN).build()
    
    # Set up notification scheduler if enabled
    if NOTIFICATION_ENABLED:
        await setup_notification_scheduler()
    
    # Set up maintenance scheduler for subscription management
    await setup_maintenance_scheduler()
    
    # Start webhook server for automatic payment processing
    asyncio.create_task(start_webhook_server())
    
    # Start analytics dashboard server (optional, won't block bot if it fails)
    try:
        asyncio.create_task(start_analytics_server())
        logger.info("Analytics dashboard server task created")
    except Exception as e:
        logger.error(f"Failed to start analytics dashboard: {e}")
        logger.info("Bot will continue without analytics dashboard")

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscription", subscription_command))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("admin", admin_command))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Add admin action handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_action_handler))

    # Add error handler
    application.add_error_handler(error_handler)

    # Initialize and start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep the application running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def run_bot():
    """Entry point to run the bot"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == '__main__':
    run_bot()
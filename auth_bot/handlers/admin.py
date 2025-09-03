# Auth Bot - handlers/admin.py

import logging
from datetime import datetime, timedelta
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from auth_bot import ADMIN_USER_IDS
from auth_bot.database.db_handler import DBManager
from auth_bot.utils.token_generator import generate_token
from auth_bot.utils.notification import NotificationManager
from auth_bot.handlers.subscription import get_plan_details

logger = logging.getLogger(__name__)


async def is_admin(user_id):
    """Check if a user is an admin
    
    Args:
        user_id: Telegram user ID
    
    Returns:
        bool: True if user is an admin, False otherwise
    """
    return user_id in ADMIN_USER_IDS


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the admin panel
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("You are not authorized to access the admin panel.")
        return
    
    # Create admin panel keyboard
    keyboard = [
        [InlineKeyboardButton("Generate Token", callback_data="admin_generate_token")],
        [InlineKeyboardButton("List Users", callback_data="admin_list_users")],
        [InlineKeyboardButton("List Subscriptions", callback_data="admin_list_subscriptions")],
        [InlineKeyboardButton("Update Subscription", callback_data="admin_update_subscription")],
        [InlineKeyboardButton("Revoke Subscription", callback_data="admin_revoke_subscription")],
        [InlineKeyboardButton("Approve Payment", callback_data="admin_approve_payment")],
        [InlineKeyboardButton("Reject Payment", callback_data="admin_reject_payment")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "*Admin Panel*\n\nSelect an action:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callback queries
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await query.answer("You are not authorized to access the admin panel.")
        return
    
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "admin_generate_token":
        await query.edit_message_text(
            "*Generate Token*\n\nPlease send the user ID and plan days in the format:\n`user_id plan_days`\n\nExample: `123456789 30`",
            parse_mode='Markdown'
        )
        context.user_data['admin_action'] = 'generate_token'
    
    elif callback_data == "admin_list_users":
        await list_users(query, context)
    
    elif callback_data == "admin_list_subscriptions":
        await list_subscriptions(query, context)
    
    elif callback_data == "admin_update_subscription":
        await query.edit_message_text(
            "*Update Subscription*\n\nPlease send the user ID and plan days in the format:\n`user_id plan_days`\n\nExample: `123456789 30`",
            parse_mode='Markdown'
        )
        context.user_data['admin_action'] = 'update_subscription'
    
    elif callback_data == "admin_revoke_subscription":
        await query.edit_message_text(
            "*Revoke Subscription*\n\nPlease send the user ID to revoke subscription:\n`user_id`\n\nExample: `123456789`",
            parse_mode='Markdown'
        )
        context.user_data['admin_action'] = 'revoke_subscription'
    
    elif callback_data == "admin_approve_payment":
        await list_pending_payments(query, context, 'approve')
    
    elif callback_data == "admin_reject_payment":
        await list_pending_payments(query, context, 'reject')


async def list_users(query, context):
    """List all users
    
    Args:
        query: Telegram callback query
        context: Telegram context object
    """
    db = DBManager()
    users = await db.get_all_users()
    
    if not users:
        await query.edit_message_text(
            "*User List*\n\nNo users found.",
            parse_mode='Markdown'
        )
        return
    
    # Create paginated list
    page = context.user_data.get('user_list_page', 0)
    page_size = 10
    total_pages = (len(users) + page_size - 1) // page_size
    
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(users))
    
    page_users = users[start_idx:end_idx]
    
    # Format user list
    user_list = "*User List*\n\n"
    for user in page_users:
        user_id = user['user_id']
        username = user.get('username', 'N/A')
        first_name = user.get('first_name', 'N/A')
        last_name = user.get('last_name', 'N/A')
        
        user_list += f"*User ID:* `{user_id}`\n"
        user_list += f"*Username:* @{username}\n"
        user_list += f"*Name:* {first_name} {last_name}\n\n"
    
    user_list += f"Page {page + 1}/{total_pages}"
    
    # Create pagination keyboard
    keyboard = []
    
    if page > 0:
        keyboard.append(InlineKeyboardButton("◀️ Previous", callback_data="admin_users_prev"))
    
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton("Next ▶️", callback_data="admin_users_next"))
    
    keyboard.append(InlineKeyboardButton("Back to Admin Panel", callback_data="admin_back"))
    
    reply_markup = InlineKeyboardMarkup([keyboard])
    
    await query.edit_message_text(
        user_list,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def list_subscriptions(query, context):
    """List all subscriptions
    
    Args:
        query: Telegram callback query
        context: Telegram context object
    """
    db = DBManager()
    subscriptions = await db.get_all_subscriptions()
    
    if not subscriptions:
        await query.edit_message_text(
            "*Subscription List*\n\nNo subscriptions found.",
            parse_mode='Markdown'
        )
        return
    
    # Create paginated list
    page = context.user_data.get('subscription_list_page', 0)
    page_size = 5
    total_pages = (len(subscriptions) + page_size - 1) // page_size
    
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(subscriptions))
    
    page_subscriptions = subscriptions[start_idx:end_idx]
    
    # Format subscription list
    subscription_list = "*Subscription List*\n\n"
    for subscription in page_subscriptions:
        user_id = subscription['user_id']
        plan_name = subscription.get('plan_name', 'N/A')
        start_date = subscription.get('start_date', 'N/A')
        expiry_date = subscription.get('expiry_date', 'N/A')
        
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d %H:%M:%S')
        
        if isinstance(expiry_date, datetime):
            expiry_date = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        
        subscription_list += f"*User ID:* `{user_id}`\n"
        subscription_list += f"*Plan:* {plan_name}\n"
        subscription_list += f"*Start Date:* {start_date}\n"
        subscription_list += f"*Expiry Date:* {expiry_date}\n\n"
    
    subscription_list += f"Page {page + 1}/{total_pages}"
    
    # Create pagination keyboard
    keyboard = []
    
    if page > 0:
        keyboard.append(InlineKeyboardButton("◀️ Previous", callback_data="admin_subscriptions_prev"))
    
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton("Next ▶️", callback_data="admin_subscriptions_next"))
    
    keyboard.append(InlineKeyboardButton("Back to Admin Panel", callback_data="admin_back"))
    
    reply_markup = InlineKeyboardMarkup([keyboard])
    
    await query.edit_message_text(
        subscription_list,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def list_pending_payments(query, context, action):
    """List pending payments
    
    Args:
        query: Telegram callback query
        context: Telegram context object
        action: Action to perform (approve or reject)
    """
    db = DBManager()
    payments = await db.get_pending_payments()
    
    if not payments:
        await query.edit_message_text(
            "*Pending Payments*\n\nNo pending payments found.",
            parse_mode='Markdown'
        )
        return
    
    # Create paginated list
    page = context.user_data.get('payment_list_page', 0)
    page_size = 5
    total_pages = (len(payments) + page_size - 1) // page_size
    
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(payments))
    
    page_payments = payments[start_idx:end_idx]
    
    # Format payment list
    payment_list = "*Pending Payments*\n\n"
    for payment in page_payments:
        payment_id = payment['payment_id']
        user_id = payment['user_id']
        amount = payment.get('amount', 'N/A')
        plan_days = payment.get('plan_days', 'N/A')
        created_at = payment.get('created_at', 'N/A')
        
        if isinstance(created_at, datetime):
            created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        payment_list += f"*Payment ID:* `{payment_id}`\n"
        payment_list += f"*User ID:* `{user_id}`\n"
        payment_list += f"*Amount:* {amount}\n"
        payment_list += f"*Plan Days:* {plan_days}\n"
        payment_list += f"*Created At:* {created_at}\n\n"
    
    payment_list += f"Page {page + 1}/{total_pages}"
    
    # Create pagination keyboard
    keyboard = []
    
    if page > 0:
        keyboard.append(InlineKeyboardButton("◀️ Previous", callback_data=f"admin_payments_prev_{action}"))
    
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton("Next ▶️", callback_data=f"admin_payments_next_{action}"))
    
    # Add action buttons
    action_keyboard = []
    for payment in page_payments:
        payment_id = payment['payment_id']
        action_keyboard.append([InlineKeyboardButton(
            f"{action.capitalize()} Payment {payment_id}", 
            callback_data=f"admin_{action}_payment_{payment_id}"
        )])
    
    action_keyboard.append([InlineKeyboardButton("Back to Admin Panel", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(action_keyboard)
    
    await query.edit_message_text(
        payment_list,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin actions
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("You are not authorized to perform this action.")
        return
    
    admin_action = context.user_data.get('admin_action')
    
    if not admin_action:
        return
    
    text = update.message.text.strip()
    
    if admin_action == 'generate_token':
        await handle_generate_token(update, context, text)
    
    elif admin_action == 'update_subscription':
        await handle_update_subscription(update, context, text)
    
    elif admin_action == 'revoke_subscription':
        await handle_revoke_subscription(update, context, text)
    
    # Clear admin action
    context.user_data['admin_action'] = None


async def handle_generate_token(update, context, text):
    """Handle generate token action
    
    Args:
        update: Telegram update object
        context: Telegram context object
        text: Message text
    """
    try:
        parts = text.split()
        
        if len(parts) != 2:
            await update.message.reply_text(
                "Invalid format. Please use: `user_id plan_days`",
                parse_mode='Markdown'
            )
            return
        
        target_user_id = int(parts[0])
        plan_days = int(parts[1])
        
        # Generate token
        token = await generate_token(target_user_id, plan_days)
        
        # Get plan name
        plan_name = await get_plan_details(plan_days)
        
        await update.message.reply_text(
            f"*Token Generated*\n\n"
            f"*User ID:* `{target_user_id}`\n"
            f"*Plan:* {plan_name}\n"
            f"*Days:* {plan_days}\n"
            f"*Token:* `{token}`\n\n"
            f"This token can be used to verify the user.",
            parse_mode='Markdown'
        )
        
        # Send notification to admin
        notification_manager = NotificationManager()
        await notification_manager.send_admin_notification(
            f"*Token Generated*\n\n"
            f"Admin: {update.effective_user.id}\n"
            f"User ID: {target_user_id}\n"
            f"Plan: {plan_name}\n"
            f"Days: {plan_days}\n"
            f"Token: {token}"
        )
        
    except ValueError:
        await update.message.reply_text(
            "Invalid input. Please provide valid user ID and plan days.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        await update.message.reply_text(
            f"Error generating token: {str(e)}",
            parse_mode='Markdown'
        )


async def handle_update_subscription(update, context, text):
    """Handle update subscription action
    
    Args:
        update: Telegram update object
        context: Telegram context object
        text: Message text
    """
    try:
        parts = text.split()
        
        if len(parts) != 2:
            await update.message.reply_text(
                "Invalid format. Please use: `user_id plan_days`",
                parse_mode='Markdown'
            )
            return
        
        target_user_id = int(parts[0])
        plan_days = int(parts[1])
        
        # Get plan name
        plan_name = await get_plan_details(plan_days)
        
        # Update subscription
        db = DBManager()
        
        # Check if user exists
        user_exists = await db.user_exists(target_user_id)
        
        if not user_exists:
            await update.message.reply_text(
                f"User with ID {target_user_id} does not exist.",
                parse_mode='Markdown'
            )
            return
        
        # Calculate expiry date
        expiry_date = datetime.now() + timedelta(days=plan_days)
        
        # Update subscription
        await db.update_subscription(
            target_user_id,
            plan_name,
            plan_days,
            expiry_date
        )
        
        await update.message.reply_text(
            f"*Subscription Updated*\n\n"
            f"*User ID:* `{target_user_id}`\n"
            f"*Plan:* {plan_name}\n"
            f"*Days:* {plan_days}\n"
            f"*Expiry Date:* {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"The user's subscription has been updated.",
            parse_mode='Markdown'
        )
        
        # Send notification to user
        notification_manager = NotificationManager()
        await notification_manager.send_subscription_activated(
            target_user_id,
            plan_name,
            expiry_date
        )
        
        # Send notification to admin
        await notification_manager.send_admin_notification(
            f"*Subscription Updated*\n\n"
            f"Admin: {update.effective_user.id}\n"
            f"User ID: {target_user_id}\n"
            f"Plan: {plan_name}\n"
            f"Days: {plan_days}\n"
            f"Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
    except ValueError:
        await update.message.reply_text(
            "Invalid input. Please provide valid user ID and plan days.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        await update.message.reply_text(
            f"Error updating subscription: {str(e)}",
            parse_mode='Markdown'
        )


async def handle_revoke_subscription(update, context, text):
    """Handle revoke subscription action
    
    Args:
        update: Telegram update object
        context: Telegram context object
        text: Message text
    """
    try:
        target_user_id = int(text.strip())
        
        # Revoke subscription
        db = DBManager()
        
        # Check if user exists
        user_exists = await db.user_exists(target_user_id)
        
        if not user_exists:
            await update.message.reply_text(
                f"User with ID {target_user_id} does not exist.",
                parse_mode='Markdown'
            )
            return
        
        # Check if subscription exists
        subscription = await db.get_subscription(target_user_id)
        
        if not subscription:
            await update.message.reply_text(
                f"User with ID {target_user_id} does not have an active subscription.",
                parse_mode='Markdown'
            )
            return
        
        # Revoke subscription
        await db.revoke_subscription(target_user_id)
        
        await update.message.reply_text(
            f"*Subscription Revoked*\n\n"
            f"*User ID:* `{target_user_id}`\n\n"
            f"The user's subscription has been revoked.",
            parse_mode='Markdown'
        )
        
        # Send notification to admin
        notification_manager = NotificationManager()
        await notification_manager.send_admin_notification(
            f"*Subscription Revoked*\n\n"
            f"Admin: {update.effective_user.id}\n"
            f"User ID: {target_user_id}"
        )
        
    except ValueError:
        await update.message.reply_text(
            "Invalid input. Please provide a valid user ID.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error revoking subscription: {e}")
        await update.message.reply_text(
            f"Error revoking subscription: {str(e)}",
            parse_mode='Markdown'
        )


async def handle_payment_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment approval or rejection
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await query.answer("You are not authorized to perform this action.")
        return
    
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("admin_approve_payment_"):
        payment_id = callback_data.replace("admin_approve_payment_", "")
        await approve_payment(query, context, payment_id)
    
    elif callback_data.startswith("admin_reject_payment_"):
        payment_id = callback_data.replace("admin_reject_payment_", "")
        await reject_payment(query, context, payment_id)


async def approve_payment(query, context, payment_id):
    """Approve a payment
    
    Args:
        query: Telegram callback query
        context: Telegram context object
        payment_id: Payment ID
    """
    try:
        db = DBManager()
        
        # Get payment details
        payment = await db.get_payment(payment_id)
        
        if not payment:
            await query.edit_message_text(
                f"Payment with ID {payment_id} not found.",
                parse_mode='Markdown'
            )
            return
        
        # Check if payment is pending
        if payment.get('status') != 'pending':
            await query.edit_message_text(
                f"Payment with ID {payment_id} is not pending.",
                parse_mode='Markdown'
            )
            return
        
        # Get payment details
        user_id = payment['user_id']
        plan_days = payment.get('plan_days', 0)
        
        # Get plan name
        plan_name = await get_plan_details(plan_days)
        
        # Calculate expiry date
        expiry_date = datetime.now() + timedelta(days=plan_days)
        
        # Update payment status
        await db.update_payment_status(payment_id, 'approved')
        
        # Update subscription
        await db.update_subscription(
            user_id,
            plan_name,
            plan_days,
            expiry_date
        )
        
        await query.edit_message_text(
            f"*Payment Approved*\n\n"
            f"*Payment ID:* `{payment_id}`\n"
            f"*User ID:* `{user_id}`\n"
            f"*Plan:* {plan_name}\n"
            f"*Days:* {plan_days}\n"
            f"*Expiry Date:* {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"The payment has been approved and the user's subscription has been updated.",
            parse_mode='Markdown'
        )
        
        # Send notification to user
        notification_manager = NotificationManager()
        await notification_manager.send_subscription_activated(
            user_id,
            plan_name,
            expiry_date
        )
        
        # Send notification to admin
        await notification_manager.send_admin_notification(
            f"*Payment Approved*\n\n"
            f"Admin: {query.from_user.id}\n"
            f"Payment ID: {payment_id}\n"
            f"User ID: {user_id}\n"
            f"Plan: {plan_name}\n"
            f"Days: {plan_days}\n"
            f"Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
    except Exception as e:
        logger.error(f"Error approving payment: {e}")
        await query.edit_message_text(
            f"Error approving payment: {str(e)}",
            parse_mode='Markdown'
        )


async def reject_payment(query, context, payment_id):
    """Reject a payment
    
    Args:
        query: Telegram callback query
        context: Telegram context object
        payment_id: Payment ID
    """
    try:
        db = DBManager()
        
        # Get payment details
        payment = await db.get_payment(payment_id)
        
        if not payment:
            await query.edit_message_text(
                f"Payment with ID {payment_id} not found.",
                parse_mode='Markdown'
            )
            return
        
        # Check if payment is pending
        if payment.get('status') != 'pending':
            await query.edit_message_text(
                f"Payment with ID {payment_id} is not pending.",
                parse_mode='Markdown'
            )
            return
        
        # Get payment details
        user_id = payment['user_id']
        
        # Update payment status
        await db.update_payment_status(payment_id, 'rejected')
        
        await query.edit_message_text(
            f"*Payment Rejected*\n\n"
            f"*Payment ID:* `{payment_id}`\n"
            f"*User ID:* `{user_id}`\n\n"
            f"The payment has been rejected.",
            parse_mode='Markdown'
        )
        
        # Send notification to user
        bot = context.bot
        await bot.send_message(
            chat_id=user_id,
            text=f"❌ *Payment Rejected* ❌\n\n"
                 f"Your payment has been rejected. Please contact the administrator for more information.",
            parse_mode='Markdown'
        )
        
        # Send notification to admin
        notification_manager = NotificationManager()
        await notification_manager.send_admin_notification(
            f"*Payment Rejected*\n\n"
            f"Admin: {query.from_user.id}\n"
            f"Payment ID: {payment_id}\n"
            f"User ID: {user_id}"
        )
        
    except Exception as e:
        logger.error(f"Error rejecting payment: {e}")
        await query.edit_message_text(
            f"Error rejecting payment: {str(e)}",
            parse_mode='Markdown'
        )
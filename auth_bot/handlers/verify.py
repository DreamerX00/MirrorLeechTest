import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from auth_bot import TARGET_BOT_USERNAME
from auth_bot.handlers.subscription import get_subscription_status
from auth_bot.utils.token_generator import generate_verification_url

logger = logging.getLogger(__name__)


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /verify command to generate a verification link.
    """
    user = update.effective_user
    user_id = user.id
    
    # Get subscription status
    subscription = await get_subscription_status(user_id)
    
    # Determine plan days based on subscription plan (0 for free tier)
    plan_days = 0
    if subscription and subscription["is_active"]:
        if subscription["plan"] == "basic":
            plan_days = 7
        elif subscription["plan"] == "standard":
            plan_days = 30
        elif subscription["plan"] == "premium":
            plan_days = 90
    
    # Generate verification URL (works for both free and paid users)
    verification_url = await generate_verification_url(user_id, plan_days)
    
    if plan_days > 0:
        # Paid subscription message
        await update.message.reply_text(
            f"🔐 *Premium Verification Link Generated*\n\n"
            f"Use this link to verify your premium access to {TARGET_BOT_USERNAME}:\n\n"
            f"{verification_url}\n\n"
            f"✅ Plan: {subscription['plan'].title()} ({plan_days} days)\n"
            f"⏰ This link will expire in 6 hours.",
            parse_mode='Markdown'
        )
    else:
        # Free tier message
        await update.message.reply_text(
            f"🆓 *Free Access Link Generated*\n\n"
            f"Use this link to get free access to {TARGET_BOT_USERNAME}:\n\n"
            f"{verification_url}\n\n"
            f"🔓 Free tier includes basic features\n"
            f"⏰ This link will expire in 6 hours\n\n"
            f"💡 Want unlimited access? Use /start to see premium plans!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 View Premium Plans", callback_data="show_plans")]
            ])
        )


async def handle_verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for verification.
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    # Acknowledge the callback query
    await query.answer()
    
    if query.data == "generate_link":
        # Get subscription status
        subscription = await get_subscription_status(user_id)
        
        if not subscription or not subscription["is_active"] or subscription["plan"] == "free":
            await query.edit_message_text(
                "❌ You need an active paid subscription to generate a verification link.\n\n"
                "Please purchase a subscription first.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 View Plans", callback_data="show_plans")],
                    [InlineKeyboardButton("🔙 Back", callback_data="start")]
                ])
            )
            return
        
        # Determine plan days based on subscription plan
        plan_days = 0
        if subscription["plan"] == "basic":
            plan_days = 7
        elif subscription["plan"] == "standard":
            plan_days = 30
        elif subscription["plan"] == "premium":
            plan_days = 90
        
        # Generate verification URL
        verification_url = await generate_verification_url(user_id, plan_days)
        
        await query.edit_message_text(
            f"🔐 *Verification Link Generated*\n\n"
            f"Use this link to verify your access to {TARGET_BOT_USERNAME}:\n\n"
            f"{verification_url}\n\n"
            f"This link will expire in 6 hours.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start")]
            ])
        )
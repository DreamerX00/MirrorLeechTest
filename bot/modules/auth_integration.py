#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from bot import bot
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters


@new_task
async def subscription_status(client, message):
    """Check user's subscription status"""
    user_id = message.from_user.id
    try:
        from auth_bot.handlers.subscription import get_subscription_status
        status = await get_subscription_status(user_id)
        if status and status.get('is_active'):
            expiry = status.get('expiry_date', 'Unknown')
            plan = status.get('plan', 'Unknown')
            msg = f"✅ **Active Subscription**\n\n📋 **Plan:** {plan}\n⏰ **Expires:** {expiry}"
        else:
            msg = "❌ **No Active Subscription**\n\nYou don't have an active subscription. Use /verify to get access."
        await sendMessage(message, msg)
    except Exception as e:
        await sendMessage(message, "❌ **Error**\n\nCould not check subscription status. Please try again later.")


@new_task
async def verify_access(client, message):
    """Generate verification link for user"""
    user_id = message.from_user.id
    try:
        from bot.helper.ext_utils.bot_utils import check_user_authorization, get_auth_button
        is_authorized, auth_message = await check_user_authorization(user_id)
        if is_authorized:
            await sendMessage(message, "✅ **Already Authorized**\n\nYou already have access to all bot features!")
        else:
            auth_button = get_auth_button(user_id)
            await sendMessage(message, "🔒 **Verification Required**\n\nClick the button below to verify your subscription and get access to all bot features.", auth_button)
    except Exception as e:
        await sendMessage(message, "❌ **Error**\n\nCould not generate verification link. Please try again later.")


# Register command handlers
bot.add_handler(
    MessageHandler(
        subscription_status,
        filters=command(BotCommands.SubscriptionCommand) & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        verify_access,
        filters=command(BotCommands.VerifyCommand) & ~CustomFilters.blacklisted,
    )
)

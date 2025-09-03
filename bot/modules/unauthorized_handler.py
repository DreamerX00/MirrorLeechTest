#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from bot import bot, config_dict
from bot.helper.ext_utils.bot_utils import new_task, get_auth_button
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters


@new_task
async def handle_unauthorized_command(client, message):
    """Handle commands from unauthorized users by redirecting to auth_bot"""
    user_id = message.from_user.id
    
    # Check if auth_bot integration is enabled
    try:
        auth_bot_enabled = config_dict.get("AUTH_BOT_ENABLED", False)
        if not auth_bot_enabled:
            # If auth_bot is disabled, show standard unauthorized message
            await sendMessage(message, "🔒 **Access Restricted**\n\nThis bot is private. Contact the owner for access.")
            return
        
        # Get auth button for redirection to auth_bot
        auth_button = get_auth_button(user_id)
        
        if auth_button is None:
            # If auth button generation fails, show fallback message
            auth_bot_username = config_dict.get("AUTH_BOT_USERNAME", "")
            if auth_bot_username:
                auth_message = f"""🔒 **Authorization Required**

To use this bot's features, you need an active subscription.

👉 **Get Access:** @{auth_bot_username}

✨ **Available Features:**
• Mirror files to Google Drive
• Leech files to Telegram  
• Support for torrents and direct links
• High-speed transfers
• Premium cloud storage

💎 **Get instant access now!**"""
            else:
                auth_message = "🔒 **Access Restricted**\n\nThis bot requires authorization. Contact the owner for access."
            
            await sendMessage(message, auth_message)
            return
        
        auth_message = """🔒 **Authorization Required**

To use this bot's features, you need an active subscription. Click the button below to get authorized access.

✨ **Available Features:**
• Mirror files to Google Drive
• Leech files to Telegram  
• Support for torrents and direct links
• High-speed transfers
• Premium cloud storage

💎 **Get instant access now!**"""
        
        await sendMessage(message, auth_message, auth_button)
        
    except Exception as e:
        # Fallback error handling
        await sendMessage(message, "🔒 **Access Restricted**\n\nThis bot is private. Contact the owner for access.")
        print(f"Error in unauthorized handler: {e}")


# Create command handlers for all main commands that require authorization
# These will only trigger for unauthorized users since authorized users are handled by the main command handlers

# Mirror commands
bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.MirrorCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.QbMirrorCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

# Leech commands
bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.LeechCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.QbLeechCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

# YT-DLP commands
bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.YtdlCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.YtdlLeechCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

# Other main commands
bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.CloneCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.CountCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.DeleteCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.ListCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.SearchCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.StatusCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.StatsCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.PingCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.BtSelectCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.CategorySelect) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.CancelMirror) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.CancelAllCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.UserSetCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.SpeedCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.RssCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.HelpCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.MediaInfoCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.IMDBCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.AniListCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

bot.add_handler(
    MessageHandler(
        handle_unauthorized_command,
        filters=command(BotCommands.MyDramaListCommand) & ~CustomFilters.authorized & ~CustomFilters.blacklisted,
    )
)

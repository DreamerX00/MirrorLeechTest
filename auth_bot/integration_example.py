# Auth Bot - Integration Example
# This file demonstrates how to integrate the authorization bot with the target WZML-X bot

# Import the integration module
from auth_bot.utils.integration import check_authorization, intercept_command, validate_verification_token

# Example of how to integrate with WZML-X bot

# 1. In the command handler of WZML-X bot, add authorization check
async def handle_command(update, context):
    user_id = update.effective_user.id
    command = update.message.text
    
    # Check if user is authorized
    is_authorized, message = await intercept_command(user_id, command)
    
    if not is_authorized:
        # User is not authorized, send verification message
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    # User is authorized, proceed with command execution
    # ... original command handling code ...


# 2. In the start command handler of WZML-X bot, add token validation
async def start(update, context):
    user_id = update.effective_user.id
    args = context.args
    
    # Check if this is a verification token
    if args and args[0].startswith('verify_'):
        token = args[0].replace('verify_', '')
        
        # Validate the token
        is_valid, message = await validate_verification_token(user_id, token)
        
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    # Regular start command handling
    # ... original start command handling code ...


# 3. Before executing any restricted command, check authorization
async def download_command(update, context):
    user_id = update.effective_user.id
    
    # Check if user is authorized
    is_authorized = await check_authorization(user_id)
    
    if not is_authorized:
        # Generate verification link and send to user
        verification_link = await generate_verification_link(user_id)
        
        await update.message.reply_text(
            f"You are not authorized to use this command. \n\n"
            f"Please verify your subscription by clicking on the link below:\n\n"
            f"{verification_link}",
            parse_mode='Markdown'
        )
        return
    
    # User is authorized, proceed with command execution
    # ... original download command handling code ...


# 4. Example of how to modify the bot_utils.py file in WZML-X
"""
# In bot_utils.py of WZML-X, modify the checking_access function

async def checking_access(user_id, button=None):
    # First check authorization with auth bot
    from auth_bot.utils.integration import check_authorization
    
    is_authorized = await check_authorization(user_id)
    
    if is_authorized:
        return True, None
    
    # If not authorized with auth bot, proceed with original logic
    # ... original checking_access code ...
"""


# 5. Example of how to modify the __main__.py file in WZML-X
"""
# In __main__.py of WZML-X, modify the token_callback function

async def token_callback(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    message = query.message
    data = query.data.split()
    
    # Check if this is an auth bot token
    if data[0] == 'auth_verify':
        from auth_bot.utils.integration import validate_verification_token
        
        token = data[1]
        is_valid, message_text = await validate_verification_token(user_id, token)
        
        await query.answer()
        await message.edit_text(message_text, parse_mode='Markdown')
        return
    
    # If not an auth bot token, proceed with original logic
    # ... original token_callback code ...
"""
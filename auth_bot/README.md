# Authorization Bot for WZML-X

This is a dedicated authorization bot designed to manage user access for the WZML-X bot. It provides a secure token-based verification system, subscription management, and payment processing capabilities.

## Features

- **Token-based Authorization**: Secure token generation and validation with 6-hour expiration
- **Subscription Management**: Tiered subscription plans (7-day, 30-day, 90-day)
- **Payment Processing**: Support for multiple payment gateways and manual approval
- **URL Shortening**: Integration with popular URL shortening services
- **Multi-bot Integration**: Designed to work with WZML-X without modifying its code
- **Admin Controls**: Comprehensive admin panel for managing users and subscriptions

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MongoDB database
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Installation

1. Clone the repository or navigate to the project directory:
   ```bash
   cd WZML-X-master
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the `auth_bot` directory using the provided `.env.sample` as a template:
   ```bash
   cp auth_bot/.env.sample auth_bot/.env
   ```

4. Edit the `.env` file with your configuration details:
   - Bot credentials (token, username)
   - Database connection details
   - Subscription plans and pricing
   - Payment gateway settings
   - Admin user IDs
   - URL shortener API keys

### Running the Bot

```bash
python -m auth_bot
```

## Integration with WZML-X

To integrate the authorization bot with WZML-X, you need to modify the command handler in WZML-X to check user authorization before executing commands. Here's a simplified example:

```python
from auth_bot.utils.integration import intercept_command

async def handle_command(update, context):
    user_id = update.effective_user.id
    command = update.message.text
    
    # Check if user is authorized
    should_proceed, message = await intercept_command(user_id, command)
    
    if not should_proceed:
        # User is not authorized, send verification message
        await update.message.reply_text(message)
        return
    
    # User is authorized, proceed with command execution
    # ... original command handling code ...
```

## Configuration Options

### Bot Settings
- `AUTH_BOT_TOKEN`: Telegram bot token for the authorization bot
- `AUTH_BOT_USERNAME`: Username of the authorization bot
- `TARGET_BOT_USERNAME`: Username of the target bot (WZML-X)

### Database Settings
- `DATABASE_URL`: MongoDB connection URL
- `DATABASE_NAME`: Name of the database

### Token Settings
- `TOKEN_SECRET_KEY`: Secret key for token encryption
- `TOKEN_TIMEOUT_HOURS`: Token expiration time in hours (default: 6)

### Subscription Plans
- `BASIC_PLAN_DAYS`: Duration of the basic plan in days
- `STANDARD_PLAN_DAYS`: Duration of the standard plan in days
- `PREMIUM_PLAN_DAYS`: Duration of the premium plan in days
- `BASIC_PLAN_PRICE`: Price of the basic plan
- `STANDARD_PLAN_PRICE`: Price of the standard plan
- `PREMIUM_PLAN_PRICE`: Price of the premium plan

### Payment Settings
- `PAYMENT_GATEWAY`: Payment gateway to use (stripe, paypal, razorpay)
- `PAYMENT_API_KEY`: API key for the payment gateway
- `PAYMENT_WEBHOOK_URL`: Webhook URL for payment notifications
- `PAYMENT_CURRENCY`: Currency for payments (USD, EUR, INR, etc.)
- `MANUAL_PAYMENT_ENABLED`: Enable manual payment approval

### Admin Settings
- `ADMIN_USER_IDS`: Comma-separated list of admin user IDs

### URL Shortener Settings
- `URL_SHORTENER_API`: URL shortener service to use (tinyurl, bitly, rebrandly, cuttly)
- `URL_SHORTENER_API_KEY`: API key for the URL shortener service

### Notification Settings
- `NOTIFICATION_ENABLED`: Enable subscription expiry notifications

## License

This project is licensed under the MIT License - see the LICENSE file for details.
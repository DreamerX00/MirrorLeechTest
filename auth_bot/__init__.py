#!/usr/bin/env python3
# Auth Bot - __init__.py

import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
AUTH_BOT_TOKEN = os.environ.get('AUTH_BOT_TOKEN')
AUTH_BOT_USERNAME = os.environ.get('AUTH_BOT_USERNAME')
TARGET_BOT_USERNAME = os.environ.get('TARGET_BOT_USERNAME')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# Token configuration
TOKEN_SECRET_KEY = os.environ.get('TOKEN_SECRET_KEY')
TOKEN_EXPIRY_HOURS = int(os.environ.get('TOKEN_EXPIRY_HOURS', 6))

# Subscription plans
BASIC_PLAN_DAYS = int(os.environ.get('BASIC_PLAN_DAYS', 7))
STANDARD_PLAN_DAYS = int(os.environ.get('STANDARD_PLAN_DAYS', 30))
PREMIUM_PLAN_DAYS = int(os.environ.get('PREMIUM_PLAN_DAYS', 90))

# Subscription prices
BASIC_PLAN_PRICE = float(os.environ.get('BASIC_PLAN_PRICE', 0))
STANDARD_PLAN_PRICE = float(os.environ.get('STANDARD_PLAN_PRICE', 0))
PREMIUM_PLAN_PRICE = float(os.environ.get('PREMIUM_PLAN_PRICE', 0))

# Payment Configuration
PAYMENT_GATEWAY = os.environ.get("PAYMENT_GATEWAY", "MANUAL")
PAYMENT_API_KEY = os.environ.get("PAYMENT_API_KEY", "")
PAYMENT_SECRET_KEY = os.environ.get("PAYMENT_SECRET_KEY", "")
PAYMENT_WEBHOOK_URL = os.environ.get("PAYMENT_WEBHOOK_URL", "")
PAYMENT_CURRENCY = os.environ.get("PAYMENT_CURRENCY", "USD")
MANUAL_PAYMENT_ENABLED = os.environ.get("MANUAL_PAYMENT_ENABLED", "true").lower() == "true"

# UPI Payment Configuration
UPI_ID = os.environ.get("UPI_ID", "")
UPI_NAME = os.environ.get("UPI_NAME", "WZML-X Subscription")

# Bank Transfer Configuration
BANK_NAME = os.environ.get("BANK_NAME", "")
ACCOUNT_NUMBER = os.environ.get("ACCOUNT_NUMBER", "")
IFSC_CODE = os.environ.get("IFSC_CODE", "")
ACCOUNT_HOLDER_NAME = os.environ.get("ACCOUNT_HOLDER_NAME", "")

# Cryptocurrency Configuration
CRYPTO_WALLET_ADDRESS = os.environ.get("CRYPTO_WALLET_ADDRESS", "")
CRYPTO_CURRENCY = os.environ.get("CRYPTO_CURRENCY", "BTC")
CRYPTO_NETWORK = os.environ.get("CRYPTO_NETWORK", "Bitcoin")

# Manual Payment Configuration
MANUAL_PAYMENT_INSTRUCTIONS = os.environ.get("MANUAL_PAYMENT_INSTRUCTIONS", "Contact admin @username with payment proof")

# Webhook Configuration
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = os.environ.get("WEBHOOK_PORT", "8080")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
WEBHOOK_SSL_CERT = os.environ.get("WEBHOOK_SSL_CERT", "")
WEBHOOK_SSL_KEY = os.environ.get("WEBHOOK_SSL_KEY", "")

# Admin configuration
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
ADMIN_USER_IDS = [int(x.strip()) for x in os.environ.get('ADMIN_USER_IDS', '').split(',') if x.strip()]

# URL shortener configuration
URL_SHORTENER_API = os.environ.get('URL_SHORTENER_API')
URL_SHORTENER_API_KEY = os.environ.get('URL_SHORTENER_API_KEY')
URL_SHORTENER_DOMAIN = os.environ.get('URL_SHORTENER_DOMAIN')
URL_SHORTENER_SECURE = os.environ.get('URL_SHORTENER_SECURE', 'true').lower() == 'true'

# Load shorteners from file if it exists
shorteners_list = []
shorteners_file = Path('.') / 'shorteners.txt'
if shorteners_file.exists():
    try:
        with open(shorteners_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) >= 3:
                        shortener = {
                            'api': parts[0].strip(),
                            'key': parts[1].strip(),
                            'domain': parts[2].strip() if len(parts) > 2 else None,
                            'secure': parts[3].strip().lower() == 'true' if len(parts) > 3 else True
                        }
                        shorteners_list.append(shortener)
        logger.info(f"Loaded {len(shorteners_list)} URL shorteners from file")
    except Exception as e:
        logger.error(f"Error loading shorteners from file: {e}")
else:
    logger.info("No shorteners.txt file found, using environment variables for URL shortening")

# Notification configuration
NOTIFY_BEFORE_EXPIRY_HOURS = int(os.environ.get('NOTIFY_BEFORE_EXPIRY_HOURS', 24))
NOTIFICATION_ENABLED = os.environ.get('NOTIFICATION_ENABLED', 'true').lower() == 'true'

# Subscription management
AUTO_REVOKE_EXPIRED = os.environ.get('AUTO_REVOKE_EXPIRED', 'true').lower() == 'true'
FREE_TIER_FALLBACK = os.environ.get('FREE_TIER_FALLBACK', 'true').lower() == 'true'
FREE_TIER_COMMANDS = os.environ.get('FREE_TIER_COMMANDS', 'help,start').split(',')

# Global variables
user_data = {}
subscription_data = {}
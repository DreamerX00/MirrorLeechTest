#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load config.env file
load_dotenv("config.env")

print("=== Environment Variables ===")
print(f"AUTH_BOT_ENABLED: {os.environ.get('AUTH_BOT_ENABLED')}")
print(f"AUTH_BOT_TOKEN: {os.environ.get('AUTH_BOT_TOKEN', 'Not set')[:20]}...")
print(f"AUTH_BOT_USERNAME: {os.environ.get('AUTH_BOT_USERNAME')}")
print(f"AUTH_BOT_TOKEN_SECRET: {os.environ.get('AUTH_BOT_TOKEN_SECRET', 'Not set')[:20]}...")

print("\n=== Config Dict Values ===")
# Manually parse values like the bot does
AUTH_BOT_ENABLED = os.environ.get("AUTH_BOT_ENABLED", "")
AUTH_BOT_ENABLED = AUTH_BOT_ENABLED.lower() == "true"
print(f"AUTH_BOT_ENABLED (parsed): {AUTH_BOT_ENABLED}")

AUTH_BOT_TOKEN = os.environ.get("AUTH_BOT_TOKEN", "")
print(f"AUTH_BOT_TOKEN (parsed): {AUTH_BOT_TOKEN[:20]}..." if AUTH_BOT_TOKEN else "Not set")

AUTH_BOT_USERNAME = os.environ.get("AUTH_BOT_USERNAME", "")
print(f"AUTH_BOT_USERNAME (parsed): {AUTH_BOT_USERNAME}")

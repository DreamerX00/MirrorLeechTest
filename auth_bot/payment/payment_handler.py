#!/usr/bin/env python3
# Auth Bot - payment/payment_handler.py

import logging
import uuid
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

# Payment gateway imports
try:
    import stripe
except ImportError:
    stripe = None

try:
    import paypalrestsdk
except ImportError:
    paypalrestsdk = None

try:
    import razorpay
except ImportError:
    razorpay = None

from auth_bot import (
    PAYMENT_GATEWAY, PAYMENT_API_KEY, PAYMENT_SECRET_KEY, PAYMENT_WEBHOOK_URL,
    MANUAL_PAYMENT_ENABLED, PAYMENT_CURRENCY, ADMIN_USER_IDS,
    BASIC_PLAN_PRICE, STANDARD_PLAN_PRICE, PREMIUM_PLAN_PRICE
)
from auth_bot.database.db_handler import DBManager
from auth_bot.utils.token_generator import generate_token

logger = logging.getLogger(__name__)

# Initialize database
db = DBManager()

async def generate_payment_link(user_id: int, plan_type: str, plan_days: int, amount: float, payment_method: str = "card") -> str:
    """
    Generate payment link based on selected payment method.
    
    Args:
        user_id: Telegram user ID
        plan_type: Subscription plan type
        plan_days: Number of days for the plan
        amount: Payment amount
        payment_method: Payment method (card, upi, netbanking, paypal)
        
    Returns:
        Payment URL string
    """
    try:
        payment_id = str(uuid.uuid4())
        
        # Store payment record in database
        payment_data = {
            "payment_id": payment_id,
            "user_id": user_id,
            "plan_type": plan_type,
            "plan_days": plan_days,
            "amount": amount,
            "payment_method": payment_method,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        await db.add_payment(payment_data)
        
        # Generate payment URL based on method
        if payment_method == "upi":
            # UPI payment link - get UPI ID from config
            from auth_bot import UPI_ID, UPI_NAME
            upi_id = UPI_ID or "your-upi-id@paytm"  # Fallback if not configured
            upi_name = UPI_NAME or "WZML-X Subscription"
            payment_url = f"upi://pay?pa={upi_id}&pn={upi_name.replace(' ', '%20')}&am={amount}&cu=USD&tn=Subscription%20{plan_type.title()}%20Plan"
            
        elif payment_method == "bank":
            # Bank transfer - show bank details page
            payment_url = f"{PAYMENT_WEBHOOK_URL}/bank_transfer/{payment_id}"
            
        elif payment_method == "crypto":
            # Cryptocurrency payment - show crypto wallet details
            payment_url = f"{PAYMENT_WEBHOOK_URL}/crypto_payment/{payment_id}"
            
        elif payment_method == "manual":
            # Manual payment - admin approval required
            payment_url = f"{PAYMENT_WEBHOOK_URL}/manual_payment/{payment_id}"
            
        elif payment_method == "paypal" and PAYMENT_API_KEY:
            # PayPal payment
            paypal = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": f"{PAYMENT_WEBHOOK_URL}/success?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment_id}",
                    "cancel_url": f"{PAYMENT_WEBHOOK_URL}/cancel?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment_id}"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"{plan_type.title()} Plan",
                            "sku": f"plan_{plan_type}",
                            "price": str(amount),
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(amount),
                        "currency": "USD"
                    },
                    "description": f"WZML-X {plan_type.title()} Plan Subscription"
                }]
            })
            
            if paypal.create():
                for link in paypal.links:
                    if link.rel == "approval_url":
                        payment_url = link.href
                        break
            else:
                logger.error(f"PayPal payment creation failed: {paypal.error}")
                payment_url = f"{PAYMENT_WEBHOOK_URL}/manual?start=payment_{payment_id}"
                
        elif payment_method == "card" and PAYMENT_API_KEY:
            # Stripe payment
            api_url = "https://api.stripe.com/v1/checkout/sessions"
            
            headers = {
                "Authorization": f"Bearer {PAYMENT_API_KEY}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Convert price to cents/smallest currency unit
            amount = int(amount * 100)
            
            # Prepare payment data
            payload = {
                "payment_method_types[0]": "card",
                "line_items[0][price_data][currency]": PAYMENT_CURRENCY.lower(),
                "line_items[0][price_data][product_data][name]": f"{plan_type.capitalize()} Plan ({plan_days} days)",
                "line_items[0][price_data][unit_amount]": amount,
                "line_items[0][quantity]": 1,
                "mode": "payment",
                "success_url": f"{PAYMENT_WEBHOOK_URL}/success?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment_id}",
                "cancel_url": f"{PAYMENT_WEBHOOK_URL}/cancel?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment_id}",
                "client_reference_id": str(user_id),
                "metadata[payment_id]": payment_id,
                "metadata[user_id]": str(user_id),
                "metadata[plan_type]": plan_type,
                "metadata[plan_days]": str(plan_days)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, data=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        payment_url = data.get("url")
                    else:
                        logger.error(f"Stripe API error: {response.status} - {await response.text()}")
                        payment_url = f"{PAYMENT_WEBHOOK_URL}/manual?start=payment_{payment_id}"
                        
        else:
            # Manual payment or fallback
            payment_url = f"{PAYMENT_WEBHOOK_URL}/manual?start=payment_{payment_id}"
        
        return payment_url
        
    except Exception as e:
        logger.error(f"Error generating payment link: {e}")
        return f"{PAYMENT_WEBHOOK_URL}/manual?start=payment_{payment_id}"

async def generate_manual_payment_link(user_id: int, plan_type: str, plan_days: int, plan_price: float) -> str:
    """
    Generate a manual payment link for admin approval.
    
    Args:
        user_id: The Telegram user ID
        plan_type: The subscription plan type
        plan_days: Number of days for the subscription
        plan_price: Price of the subscription plan
        
    Returns:
        A deep link to the bot with payment information
    """
    try:
        # Generate a unique payment ID
        payment_id = str(uuid.uuid4())
        
        # Add payment record to database
        await db.add_payment(user_id, plan_price, plan_type, payment_id, "pending")
        
        # Create a deep link with payment information
        payment_data = {
            "user_id": user_id,
            "plan_type": plan_type,
            "plan_days": plan_days,
            "plan_price": plan_price,
            "payment_id": payment_id
        }
        
        # Encode payment data as a query parameter
        payment_data_str = json.dumps(payment_data)
        
        # Return a deep link to the bot with payment information
        return f"https://t.me/admin_payment_approval?start=payment_{payment_id}"
    except Exception as e:
        logger.error(f"Error generating manual payment link: {e}")
        return "https://t.me/admin_payment_approval"

async def generate_stripe_payment_link(user_id: int, plan_type: str, plan_days: int, plan_price: float) -> Optional[str]:
    """
    Generate a Stripe payment link.
    
    Args:
        user_id: The Telegram user ID
        plan_type: The subscription plan type
        plan_days: Number of days for the subscription
        plan_price: Price of the subscription plan
        
    Returns:
        The Stripe payment link if successful, None otherwise
    """
    try:
        # Generate a unique payment ID
        payment_id = str(uuid.uuid4())
        
        # Add payment record to database
        await db.add_payment(user_id, plan_price, plan_type, payment_id, "pending")
        
        # Create Stripe payment session
        api_url = "https://api.stripe.com/v1/checkout/sessions"
        
        headers = {
            "Authorization": f"Bearer {PAYMENT_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Convert price to cents/smallest currency unit
        amount = int(plan_price * 100)
        
        # Prepare payment data
        payload = {
            "payment_method_types[0]": "card",
            "line_items[0][price_data][currency]": PAYMENT_CURRENCY.lower(),
            "line_items[0][price_data][product_data][name]": f"{plan_type.capitalize()} Plan ({plan_days} days)",
            "line_items[0][price_data][unit_amount]": amount,
            "line_items[0][quantity]": 1,
            "mode": "payment",
            "success_url": f"{PAYMENT_WEBHOOK_URL}/success?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment_id}",
            "cancel_url": f"{PAYMENT_WEBHOOK_URL}/cancel?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment_id}",
            "client_reference_id": str(user_id),
            "metadata[payment_id]": payment_id,
            "metadata[user_id]": str(user_id),
            "metadata[plan_type]": plan_type,
            "metadata[plan_days]": str(plan_days)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, data=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("url")
                else:
                    logger.error(f"Stripe API error: {response.status} - {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error generating Stripe payment link: {e}")
        return None

async def generate_paypal_payment_link(user_id: int, plan_type: str, plan_days: int, plan_price: float) -> Optional[str]:
    """
    Generate a PayPal payment link.
    
    Args:
        user_id: The Telegram user ID
        plan_type: The subscription plan type
        plan_days: Number of days for the subscription
        plan_price: Price of the subscription plan
        
    Returns:
        The PayPal payment link if successful, None otherwise
    """
    try:
        # Generate a unique payment ID
        payment_id = str(uuid.uuid4())
        
        # Add payment record to database
        await db.add_payment(user_id, plan_price, plan_type, payment_id, "pending")
        
        # Create PayPal order
        api_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"  # Use sandbox for testing
        
        headers = {
            "Authorization": f"Bearer {PAYMENT_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare payment data
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": payment_id,
                    "description": f"{plan_type.capitalize()} Plan ({plan_days} days)",
                    "custom_id": str(user_id),
                    "amount": {
                        "currency_code": PAYMENT_CURRENCY.upper(),
                        "value": str(plan_price)
                    }
                }
            ],
            "application_context": {
                "return_url": f"{PAYMENT_WEBHOOK_URL}/success?payment_id={payment_id}",
                "cancel_url": f"{PAYMENT_WEBHOOK_URL}/cancel?payment_id={payment_id}"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                if response.status == 201:
                    data = await response.json()
                    
                    # Find the approval URL
                    for link in data.get("links", []):
                        if link.get("rel") == "approve":
                            return link.get("href")
                    
                    return None
                else:
                    logger.error(f"PayPal API error: {response.status} - {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error generating PayPal payment link: {e}")
        return None

async def generate_razorpay_payment_link(user_id: int, plan_type: str, plan_days: int, plan_price: float) -> Optional[str]:
    """
    Generate a Razorpay payment link.
    
    Args:
        user_id: The Telegram user ID
        plan_type: The subscription plan type
        plan_days: Number of days for the subscription
        plan_price: Price of the subscription plan
        
    Returns:
        The Razorpay payment link if successful, None otherwise
    """
    try:
        # Generate a unique payment ID
        payment_id = str(uuid.uuid4())
        
        # Add payment record to database
        await db.add_payment(user_id, plan_price, plan_type, payment_id, "pending")
        
        # Create Razorpay payment link
        api_url = "https://api.razorpay.com/v1/payment_links"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Convert price to smallest currency unit (paise for INR)
        amount = int(plan_price * 100)
        
        # Prepare payment data
        payload = {
            "amount": amount,
            "currency": PAYMENT_CURRENCY.upper(),
            "accept_partial": False,
            "description": f"{plan_type.capitalize()} Plan ({plan_days} days)",
            "customer": {
                "name": f"User {user_id}",
                "contact": "+910000000000",  # Placeholder
                "email": f"user{user_id}@example.com"  # Placeholder
            },
            "notify": {
                "sms": False,
                "email": False
            },
            "reminder_enable": False,
            "notes": {
                "payment_id": payment_id,
                "user_id": str(user_id),
                "plan_type": plan_type,
                "plan_days": str(plan_days)
            },
            "callback_url": f"{PAYMENT_WEBHOOK_URL}/razorpay?payment_id={payment_id}",
            "callback_method": "get"
        }
        
        # Use both API key (key_id) and secret key for authentication
        auth = aiohttp.BasicAuth(PAYMENT_API_KEY, PAYMENT_SECRET_KEY)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("short_url")
                else:
                    logger.error(f"Razorpay API error: {response.status} - {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error generating Razorpay payment link: {e}")
        return None

async def process_payment(payment_id: str, status: str) -> bool:
    """
    Process a payment and update the user's subscription if successful.
    
    Args:
        payment_id: The payment ID
        status: The payment status (success, failed, pending)
        
    Returns:
        True if the payment was processed successfully, False otherwise
    """
    try:
        # Update payment status in database
        await db.update_payment_status(payment_id, status)
        
        if status.lower() != "success":
            logger.info(f"Payment {payment_id} status updated to {status}, but not successful")
            return False
        
        # Get payment details
        payment = await db.get_payment(payment_id)
        
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            return False
        
        user_id = payment.get("user_id")
        plan_type = payment.get("plan_type")
        
        if not user_id or not plan_type:
            logger.error(f"Invalid payment data for {payment_id}")
            return False
        
        # Determine plan days based on plan type
        if plan_type == "basic":
            plan_days = 30
        elif plan_type == "standard":
            plan_days = 90
        elif plan_type == "premium":
            plan_days = 180
        else:
            logger.error(f"Invalid plan type: {plan_type}")
            return False
        
        # Generate token for the user
        token = generate_token(user_id, plan_days)
        
        # Add token to database
        expires_at = datetime.now() + timedelta(hours=6)  # 6-hour expiration
        await db.add_token(token, user_id, expires_at)
        
        # Update user subscription
        from auth_bot.handlers.subscription import update_subscription
        await update_subscription(user_id, plan_days)
        
        logger.info(f"Payment {payment_id} processed successfully for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        return False

async def approve_manual_payment(payment_id: str, admin_id: int) -> bool:
    """
    Approve a manual payment.
    
    Args:
        payment_id: The payment ID
        admin_id: The admin user ID
        
    Returns:
        True if the payment was approved successfully, False otherwise
    """
    try:
        # Check if admin is authorized
        if admin_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized admin approval attempt by user {admin_id}")
            return False
        
        # Process the payment as successful
        success = await process_payment(payment_id, "success")
        
        if success:
            logger.info(f"Manual payment {payment_id} approved by admin {admin_id}")
        else:
            logger.error(f"Failed to approve manual payment {payment_id}")
        
        return success
    except Exception as e:
        logger.error(f"Error approving manual payment: {e}")
        return False

async def reject_manual_payment(payment_id: str, admin_id: int) -> bool:
    """
    Reject a manual payment.
    
    Args:
        payment_id: The payment ID
        admin_id: The admin user ID
        
    Returns:
        True if the payment was rejected successfully, False otherwise
    """
    try:
        # Check if admin is authorized
        if admin_id not in ADMIN_USER_IDS:
            logger.warning(f"Unauthorized admin rejection attempt by user {admin_id}")
            return False
        
        # Update payment status to rejected
        success = await db.update_payment_status(payment_id, "rejected")
        
        if success:
            logger.info(f"Manual payment {payment_id} rejected by admin {admin_id}")
        else:
            logger.error(f"Failed to reject manual payment {payment_id}")
        
        return success
    except Exception as e:
        logger.error(f"Error rejecting manual payment: {e}")
        return False

async def handle_razorpay_webhook(request_data: Dict[str, Any]) -> bool:
    """
    Handle Razorpay webhook callback.
    
    Args:
        request_data: The webhook request data
        
    Returns:
        True if the webhook was processed successfully, False otherwise
    """
    try:
        # Verify webhook signature if provided
        if 'razorpay_signature' in request_data:
            # TODO: Implement signature verification using PAYMENT_SECRET_KEY
            pass
        
        # Extract payment details
        payment_id = request_data.get('notes', {}).get('payment_id')
        payment_status = request_data.get('status')
        
        if not payment_id or not payment_status:
            logger.error(f"Invalid Razorpay webhook data: {request_data}")
            return False
        
        # Map Razorpay status to our status
        status_mapping = {
            'paid': 'success',
            'authorized': 'success',
            'captured': 'success',
            'refunded': 'refunded',
            'failed': 'failed'
        }
        
        our_status = status_mapping.get(payment_status.lower(), 'pending')
        
        # Process the payment
        success = await process_payment(payment_id, our_status)
        
        if success:
            logger.info(f"Razorpay webhook processed successfully for payment {payment_id}")
        else:
            logger.error(f"Failed to process Razorpay webhook for payment {payment_id}")
        
        return success
    except Exception as e:
        logger.error(f"Error processing Razorpay webhook: {e}")
        return False
#!/usr/bin/env python3
# Auth Bot - Webhook Server for Payment Automation

import asyncio
import logging
import json
from aiohttp import web, web_request
from datetime import datetime

from auth_bot import (
    WEBHOOK_HOST, WEBHOOK_PORT, WEBHOOK_SECRET, 
    WEBHOOK_SSL_CERT, WEBHOOK_SSL_KEY
)
from auth_bot.webhook_handler import webhook_handler

logger = logging.getLogger(__name__)

class WebhookServer:
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Setup webhook routes"""
        self.app.router.add_post('/webhook/stripe', self.stripe_webhook)
        self.app.router.add_post('/webhook/paypal', self.paypal_webhook)
        self.app.router.add_post('/webhook/upi', self.upi_webhook)
        self.app.router.add_get('/payment/success/{payment_id}', self.payment_success)
        self.app.router.add_get('/payment/cancel/{payment_id}', self.payment_cancel)
        self.app.router.add_get('/payment/manual/{payment_id}', self.manual_payment)
        self.app.router.add_get('/bank_transfer/{payment_id}', self.bank_transfer_page)
        self.app.router.add_get('/crypto_payment/{payment_id}', self.crypto_payment_page)
        self.app.router.add_get('/manual_payment/{payment_id}', self.manual_payment_page)
        self.app.router.add_post('/confirm_payment/{payment_id}', self.confirm_payment)
        self.app.router.add_get('/health', self.health_check)

    async def stripe_webhook(self, request: web_request.Request):
        """Handle Stripe webhook"""
        try:
            payload = await request.json()
            
            # Verify webhook signature if secret is configured
            if WEBHOOK_SECRET:
                signature = request.headers.get('stripe-signature')
                # Add signature verification logic here
            
            success = await webhook_handler.handle_stripe_webhook(payload)
            
            if success:
                return web.json_response({'status': 'success'})
            else:
                return web.json_response({'status': 'error'}, status=400)
                
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            return web.json_response({'status': 'error'}, status=500)

    async def paypal_webhook(self, request: web_request.Request):
        """Handle PayPal webhook"""
        try:
            payload = await request.json()
            
            success = await webhook_handler.handle_paypal_webhook(payload)
            
            if success:
                return web.json_response({'status': 'success'})
            else:
                return web.json_response({'status': 'error'}, status=400)
                
        except Exception as e:
            logger.error(f"PayPal webhook error: {e}")
            return web.json_response({'status': 'error'}, status=500)

    async def upi_webhook(self, request: web_request.Request):
        """Handle UPI payment confirmation webhook"""
        try:
            data = await request.json()
            payment_id = data.get('payment_id')
            transaction_id = data.get('transaction_id')
            
            if not payment_id or not transaction_id:
                return web.json_response({'status': 'missing_data'}, status=400)
            
            success = await webhook_handler.handle_upi_confirmation(payment_id, transaction_id)
            
            if success:
                return web.json_response({'status': 'success'})
            else:
                return web.json_response({'status': 'error'}, status=400)
                
        except Exception as e:
            logger.error(f"UPI webhook error: {e}")
            return web.json_response({'status': 'error'}, status=500)

    async def payment_success(self, request: web_request.Request):
        """Handle payment success redirect"""
        payment_id = request.match_info['payment_id']
        
        return web.Response(
            text=f"""
            <html>
            <head><title>Payment Successful</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✅ Payment Successful!</h1>
                <p>Your subscription has been activated automatically.</p>
                <p>Payment ID: {payment_id}</p>
                <p>You can now close this window and return to Telegram.</p>
            </body>
            </html>
            """,
            content_type='text/html'
        )

    async def payment_cancel(self, request: web_request.Request):
        """Handle payment cancellation"""
        payment_id = request.match_info['payment_id']
        
        return web.Response(
            text=f"""
            <html>
            <head><title>Payment Cancelled</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: orange;">❌ Payment Cancelled</h1>
                <p>Your payment was cancelled.</p>
                <p>Payment ID: {payment_id}</p>
                <p>You can return to Telegram and try again.</p>
            </body>
            </html>
            """,
            content_type='text/html'
        )

    async def manual_payment(self, request: web_request.Request):
        """Handle manual payment page"""
        payment_id = request.match_info['payment_id']
        
        return web.Response(
            text=f"""
            <html>
            <head><title>Manual Payment</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>💳 Manual Payment</h1>
                <p>Please contact the administrator to complete your payment.</p>
                <p>Payment ID: <strong>{payment_id}</strong></p>
                <p>Provide this Payment ID to the admin for verification.</p>
                <p>You can close this window and return to Telegram.</p>
            </body>
            </html>
            """,
            content_type='text/html'
        )

    async def bank_transfer_page(self, request: web_request.Request):
        """Handle bank transfer page"""
        payment_id = request.match_info['payment_id']
        
        return web.Response(
            text=f"""
            <html>
            <head><title>Bank Transfer</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>🏦 Bank Transfer</h1>
                <p>Please make the payment to the following account:</p>
                <p>Account Number: XXXXXXXXXX</p>
                <p>Account Name: XXXXXXXXXX</p>
                <p>Bank Name: XXXXXXXXXX</p>
                <p>Payment ID: <strong>{payment_id}</strong></p>
                <p>Provide this Payment ID to the admin for verification.</p>
                <p>You can close this window and return to Telegram.</p>
            </body>
            </html>
            """,
            content_type='text/html'
        )

    async def crypto_payment_page(self, request: web_request.Request):
        """Handle crypto payment page"""
        payment_id = request.match_info['payment_id']
        
        return web.Response(
            text=f"""
            <html>
            <head><title>Crypto Payment</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>💸 Crypto Payment</h1>
                <p>Please make the payment to the following wallet:</p>
                <p>Wallet Address: XXXXXXXXXX</p>
                <p>Payment ID: <strong>{payment_id}</strong></p>
                <p>Provide this Payment ID to the admin for verification.</p>
                <p>You can close this window and return to Telegram.</p>
            </body>
            </html>
            """,
            content_type='text/html'
        )

    async def manual_payment_page(self, request: web_request.Request):
        """Handle manual payment page"""
        payment_id = request.match_info['payment_id']
        
        return web.Response(
            text=f"""
            <html>
            <head><title>Manual Payment</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>💳 Manual Payment</h1>
                <p>Please contact the administrator to complete your payment.</p>
                <p>Payment ID: <strong>{payment_id}</strong></p>
                <p>Provide this Payment ID to the admin for verification.</p>
                <p>You can close this window and return to Telegram.</p>
            </body>
            </html>
            """,
            content_type='text/html'
        )

    async def confirm_payment(self, request: web_request.Request):
        """Handle payment confirmation"""
        payment_id = request.match_info['payment_id']
        
        try:
            data = await request.json()
            payment_method = data.get('payment_method')
            
            if payment_method == 'bank_transfer':
                success = await webhook_handler.handle_bank_transfer_confirmation(payment_id)
            elif payment_method == 'crypto':
                success = await webhook_handler.handle_crypto_confirmation(payment_id)
            elif payment_method == 'manual':
                success = await webhook_handler.handle_manual_confirmation(payment_id)
            else:
                return web.json_response({'status': 'invalid_payment_method'}, status=400)
            
            if success:
                return web.json_response({'status': 'success'})
            else:
                return web.json_response({'status': 'error'}, status=400)
                
        except Exception as e:
            logger.error(f"Payment confirmation error: {e}")
            return web.json_response({'status': 'error'}, status=500)

    async def health_check(self, request: web_request.Request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'auth_bot_webhook'
        })

    async def start_server(self):
        """Start the webhook server"""
        try:
            # Setup SSL if certificates are provided
            ssl_context = None
            if WEBHOOK_SSL_CERT and WEBHOOK_SSL_KEY:
                import ssl
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_KEY)
                logger.info("SSL enabled for webhook server")
            
            # Start server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(
                runner, 
                WEBHOOK_HOST, 
                int(WEBHOOK_PORT),
                ssl_context=ssl_context
            )
            
            await site.start()
            
            protocol = "https" if ssl_context else "http"
            logger.info(f"Webhook server started on {protocol}://{WEBHOOK_HOST}:{WEBHOOK_PORT}")
            
            # Keep server running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
                
        except Exception as e:
            logger.error(f"Error starting webhook server: {e}")

# Global webhook server instance
webhook_server = WebhookServer()

async def start_webhook_server():
    """Start the webhook server"""
    await webhook_server.start_server()

if __name__ == "__main__":
    asyncio.run(start_webhook_server())

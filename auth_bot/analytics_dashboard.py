#!/usr/bin/env python3
# Auth Bot - Analytics Dashboard

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from aiohttp import web, web_request
import json

from auth_bot import ADMIN_USER_IDS, WEBHOOK_HOST, WEBHOOK_PORT
from auth_bot.database.db_handler import DBManager

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    def __init__(self):
        self.db = DBManager()
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup analytics dashboard routes"""
        self.app.router.add_get('/analytics', self.dashboard_home)
        self.app.router.add_get('/analytics/payments', self.payments_dashboard)
        self.app.router.add_get('/analytics/subscriptions', self.subscriptions_dashboard)
        self.app.router.add_get('/analytics/users', self.users_dashboard)
        self.app.router.add_get('/analytics/usage', self.usage_dashboard)
        
        # API endpoints
        self.app.router.add_get('/api/analytics/summary', self.api_analytics_summary)
        self.app.router.add_get('/api/analytics/payments', self.api_payment_analytics)
        self.app.router.add_get('/api/analytics/subscriptions', self.api_subscription_analytics)
        self.app.router.add_get('/api/analytics/users', self.api_user_analytics)
        self.app.router.add_get('/api/analytics/usage', self.api_usage_analytics)
    
    async def verify_admin(self, request: web_request.Request) -> bool:
        """Verify admin access for dashboard"""
        admin_key = request.query.get('admin_key')
        return admin_key == "admin_dashboard_key"  # Replace with secure auth
    
    async def dashboard_home(self, request: web_request.Request):
        """Main analytics dashboard"""
        if not await self.verify_admin(request):
            return web.Response(text="Unauthorized", status=401)
        
        summary = await self.db.get_analytics_summary(30)
        payment_analytics = await self.db.get_payment_analytics(30)
        subscription_analytics = await self.db.get_subscription_analytics(30)
        user_analytics = await self.db.get_user_analytics(30)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WZML-X Auth Bot Analytics</title>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 2em; font-weight: bold; color: #3498db; }}
                .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
                .chart-container {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .nav-links {{ margin: 20px 0; }}
                .nav-links a {{ margin-right: 20px; padding: 10px 15px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 WZML-X Auth Bot Analytics</h1>
                    <p>Real-time subscription and payment analytics dashboard</p>
                </div>
                
                <div class="nav-links">
                    <a href="/analytics">🏠 Overview</a>
                    <a href="/analytics/payments">💳 Payments</a>
                    <a href="/analytics/subscriptions">📋 Subscriptions</a>
                    <a href="/analytics/users">👥 Users</a>
                    <a href="/analytics/usage">📈 Usage</a>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${summary.get('total_revenue', 0):.2f}</div>
                        <div class="stat-label">Total Revenue (30 days)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{user_analytics.get('total_users', 0)}</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{subscription_analytics.get('active_subscriptions', 0)}</div>
                        <div class="stat-label">Active Subscriptions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(payment_analytics.get('payment_status', []))}</div>
                        <div class="stat-label">Payments (30 days)</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>📈 Daily Revenue Trend</h3>
                    <canvas id="revenueChart" width="400" height="200"></canvas>
                </div>
            </div>
            
            <script>
                const revenueData = {json.dumps(payment_analytics.get('daily_revenue', []))};
                const ctx = document.getElementById('revenueChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: revenueData.map(d => d._id),
                        datasets: [{{
                            label: 'Daily Revenue ($)',
                            data: revenueData.map(d => d.revenue),
                            borderColor: '#3498db',
                            tension: 0.4
                        }}]
                    }},
                    options: {{ responsive: true }}
                }});
            </script>
        </body>
        </html>
        """
        
        return web.Response(text=html, content_type='text/html')
    
    # API Endpoints
    async def api_analytics_summary(self, request: web_request.Request):
        """API endpoint for analytics summary"""
        if not await self.verify_admin(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        days = int(request.query.get('days', 30))
        summary = await self.db.get_analytics_summary(days)
        return web.json_response(summary)

# Global dashboard instance
analytics_dashboard = AnalyticsDashboard()

async def start_analytics_server():
    """Start the analytics dashboard server"""
    try:
        await analytics_dashboard.db.connect()
        
        runner = web.AppRunner(analytics_dashboard.app)
        await runner.setup()
        
        analytics_port = int(WEBHOOK_PORT) + 1
        site = web.TCPSite(runner, WEBHOOK_HOST, analytics_port)
        await site.start()
        
        logger.info(f"Analytics dashboard started on http://{WEBHOOK_HOST}:{analytics_port}/analytics")
        
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.error(f"Error starting analytics server: {e}")

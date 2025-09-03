#!/usr/bin/env python3
# Auth Bot - Database Models and Schema

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str] = None
    created_at: datetime = None
    last_active: datetime = None
    is_banned: bool = False
    referral_code: Optional[str] = None
    referred_by: Optional[int] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()

@dataclass
class Subscription:
    user_id: int
    plan_type: str
    plan_days: int
    start_date: datetime
    end_date: datetime
    status: str = SubscriptionStatus.ACTIVE.value
    payment_id: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE.value and datetime.now() < self.end_date
    
    @property
    def days_remaining(self) -> int:
        if self.is_active:
            return max(0, (self.end_date - datetime.now()).days)
        return 0

@dataclass
class Payment:
    payment_id: str
    user_id: int
    plan_type: str
    plan_days: int
    amount: float
    currency: str
    payment_method: str
    status: str = PaymentStatus.PENDING.value
    gateway_payment_id: Optional[str] = None
    gateway_response: Optional[Dict] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class Token:
    token: str
    user_id: int
    plan_days: int
    expires_at: datetime
    used: bool = False
    created_at: datetime = None
    used_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def is_valid(self) -> bool:
        return not self.used and datetime.now() < self.expires_at

@dataclass
class UsageStats:
    user_id: int
    command: str
    timestamp: datetime
    success: bool = True
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class Analytics:
    date: datetime
    total_users: int = 0
    active_users: int = 0
    new_users: int = 0
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    expired_subscriptions: int = 0
    total_payments: int = 0
    successful_payments: int = 0
    failed_payments: int = 0
    revenue: float = 0.0
    commands_executed: int = 0
    
    def __post_init__(self):
        if not hasattr(self, 'date') or self.date is None:
            self.date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Database Schema Definitions
COLLECTIONS = {
    'users': {
        'indexes': [
            {'keys': [('user_id', 1)], 'unique': True},
            {'keys': [('username', 1)]},
            {'keys': [('created_at', -1)]},
            {'keys': [('referral_code', 1)], 'unique': True, 'sparse': True}
        ]
    },
    'subscriptions': {
        'indexes': [
            {'keys': [('user_id', 1), ('created_at', -1)]},
            {'keys': [('status', 1)]},
            {'keys': [('end_date', 1)]},
            {'keys': [('payment_id', 1)]}
        ]
    },
    'payments': {
        'indexes': [
            {'keys': [('payment_id', 1)], 'unique': True},
            {'keys': [('user_id', 1), ('created_at', -1)]},
            {'keys': [('status', 1)]},
            {'keys': [('payment_method', 1)]},
            {'keys': [('gateway_payment_id', 1)]}
        ]
    },
    'tokens': {
        'indexes': [
            {'keys': [('token', 1)], 'unique': True},
            {'keys': [('user_id', 1)]},
            {'keys': [('expires_at', 1)]},
            {'keys': [('used', 1)]}
        ]
    },
    'usage_stats': {
        'indexes': [
            {'keys': [('user_id', 1), ('timestamp', -1)]},
            {'keys': [('command', 1)]},
            {'keys': [('timestamp', -1)]},
            {'keys': [('success', 1)]}
        ]
    },
    'analytics': {
        'indexes': [
            {'keys': [('date', 1)], 'unique': True}
        ]
    }
}

def to_dict(obj) -> Dict[str, Any]:
    """Convert dataclass to dictionary for MongoDB storage"""
    if hasattr(obj, '__dict__'):
        return asdict(obj)
    return obj

def from_dict(data: Dict[str, Any], model_class) -> Any:
    """Convert dictionary from MongoDB to dataclass"""
    if data is None:
        return None
    
    # Remove MongoDB _id field if present
    if '_id' in data:
        del data['_id']
    
    return model_class(**data)

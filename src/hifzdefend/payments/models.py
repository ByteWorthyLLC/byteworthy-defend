"""Payment data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class BillingInterval(str, Enum):
    """Billing intervals."""

    MONTH = "month"
    YEAR = "year"


class ProductType(str, Enum):
    """Product types."""

    LICENSE = "license"
    SUBSCRIPTION = "subscription"


class PaymentStatus(str, Enum):
    """Payment status."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionStatus(str, Enum):
    """Subscription status."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"


class Product(BaseModel):
    """Product model."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    product_type: ProductType = Field(..., description="Product type")
    license_type: str = Field(..., description="Associated license type")
    features: list[str] = Field(default_factory=list, description="Feature list")
    metadata: dict = Field(default_factory=dict)


class Price(BaseModel):
    """Price model."""

    id: str = Field(..., description="Price ID")
    product_id: str = Field(..., description="Associated product ID")
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    billing_interval: Optional[BillingInterval] = Field(None, description="Billing interval for subscriptions")
    trial_days: int = Field(default=0, description="Trial period in days")
    active: bool = Field(default=True)


class CheckoutSession(BaseModel):
    """Stripe checkout session."""

    id: str = Field(..., description="Session ID")
    customer_email: str = Field(..., description="Customer email")
    product_id: str = Field(..., description="Product ID")
    price_id: str = Field(..., description="Price ID")
    success_url: str = Field(..., description="Success redirect URL")
    cancel_url: str = Field(..., description="Cancel redirect URL")
    checkout_url: Optional[str] = Field(None, description="Stripe checkout URL")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Subscription(BaseModel):
    """Subscription model."""

    id: str = Field(..., description="Subscription ID")
    customer_id: str = Field(..., description="Stripe customer ID")
    customer_email: str = Field(..., description="Customer email")
    product_id: str = Field(..., description="Product ID")
    price_id: str = Field(..., description="Price ID")
    status: SubscriptionStatus = Field(..., description="Subscription status")
    current_period_start: datetime = Field(..., description="Current billing period start")
    current_period_end: datetime = Field(..., description="Current billing period end")
    cancel_at_period_end: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    license_key: Optional[str] = Field(None, description="Associated license key")


class PaymentIntent(BaseModel):
    """Payment intent model."""

    id: str = Field(..., description="Payment intent ID")
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd")
    status: PaymentStatus = Field(..., description="Payment status")
    customer_email: Optional[str] = Field(None)
    product_id: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

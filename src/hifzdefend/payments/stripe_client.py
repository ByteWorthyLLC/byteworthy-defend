"""Stripe payment integration."""

import logging
from typing import Optional
from datetime import datetime, timedelta

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from .models import (
    Product,
    Price,
    CheckoutSession,
    Subscription,
    PaymentStatus,
    SubscriptionStatus,
    BillingInterval,
)

logger = logging.getLogger(__name__)


class StripeClient:
    """Stripe API client wrapper."""

    def __init__(self, api_key: str, webhook_secret: Optional[str] = None):
        """Initialize Stripe client.

        Args:
            api_key: Stripe secret API key
            webhook_secret: Webhook signing secret
        """
        if not STRIPE_AVAILABLE:
            raise ImportError("stripe package not installed. Run: pip install stripe")

        stripe.api_key = api_key
        self.webhook_secret = webhook_secret

    def create_product(self, product: Product) -> str:
        """Create product in Stripe.

        Args:
            product: Product to create

        Returns:
            Stripe product ID
        """
        stripe_product = stripe.Product.create(
            name=product.name,
            description=product.description,
            metadata={
                "license_type": product.license_type,
                "product_type": product.product_type,
                **product.metadata,
            },
        )

        return stripe_product.id

    def create_price(self, price: Price) -> str:
        """Create price in Stripe.

        Args:
            price: Price to create

        Returns:
            Stripe price ID
        """
        price_data = {
            "product": price.product_id,
            "currency": price.currency,
            "unit_amount": price.amount,
        }

        # Add recurring billing if specified
        if price.billing_interval:
            price_data["recurring"] = {
                "interval": price.billing_interval,
                "trial_period_days": price.trial_days if price.trial_days > 0 else None,
            }

        stripe_price = stripe.Price.create(**price_data)

        return stripe_price.id

    def create_checkout_session(self, session: CheckoutSession) -> str:
        """Create Stripe checkout session.

        Args:
            session: Checkout session details

        Returns:
            Checkout session URL
        """
        stripe_session = stripe.checkout.Session.create(
            customer_email=session.customer_email,
            line_items=[
                {
                    "price": session.price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription" if session.price_id.startswith("price_") else "payment",
            success_url=session.success_url,
            cancel_url=session.cancel_url,
            metadata={
                "product_id": session.product_id,
                "customer_email": session.customer_email,
            },
        )

        return stripe_session.url

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription details.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription details or None
        """
        try:
            sub = stripe.Subscription.retrieve(subscription_id)

            return Subscription(
                id=sub.id,
                customer_id=sub.customer,
                customer_email=sub.metadata.get("customer_email", ""),
                product_id=sub.metadata.get("product_id", ""),
                price_id=sub.items.data[0].price.id,
                status=SubscriptionStatus(sub.status),
                current_period_start=datetime.fromtimestamp(sub.current_period_start),
                current_period_end=datetime.fromtimestamp(sub.current_period_end),
                cancel_at_period_end=sub.cancel_at_period_end,
                created_at=datetime.fromtimestamp(sub.created),
            )

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {e}")
            return None

    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Whether to cancel at period end or immediately

        Returns:
            Success status
        """
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.cancel(subscription_id)

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """Verify webhook signature and parse event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header value

        Returns:
            Parsed webhook event

        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
        """
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        return stripe.Webhook.construct_event(
            payload,
            signature,
            self.webhook_secret
        )


class PaymentService:
    """High-level payment service."""

    def __init__(self, stripe_client: StripeClient):
        """Initialize payment service.

        Args:
            stripe_client: Stripe client instance
        """
        self.stripe = stripe_client

    def create_trial_checkout(self, email: str, success_url: str, cancel_url: str) -> str:
        """Create checkout session for trial license.

        Args:
            email: Customer email
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL

        Returns:
            Checkout URL
        """
        # This would reference a pre-created trial product/price in Stripe
        session = CheckoutSession(
            id="",  # Generated by Stripe
            customer_email=email,
            product_id="prod_trial",  # Replace with actual Stripe product ID
            price_id="price_trial",  # Replace with actual Stripe price ID
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return self.stripe.create_checkout_session(session)

    def create_license_checkout(
        self,
        email: str,
        license_type: str,
        success_url: str,
        cancel_url: str
    ) -> str:
        """Create checkout session for license purchase.

        Args:
            email: Customer email
            license_type: License type (personal, professional, enterprise)
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL

        Returns:
            Checkout URL
        """
        # Map license types to Stripe price IDs
        price_map = {
            "personal": "price_personal_annual",
            "professional": "price_professional_annual",
            "enterprise": "price_enterprise_annual",
        }

        price_id = price_map.get(license_type)
        if not price_id:
            raise ValueError(f"Invalid license type: {license_type}")

        session = CheckoutSession(
            id="",
            customer_email=email,
            product_id=f"prod_{license_type}",
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return self.stripe.create_checkout_session(session)

    def handle_payment_success(self, session_id: str) -> dict:
        """Handle successful payment.

        Args:
            session_id: Stripe checkout session ID

        Returns:
            Payment details
        """
        # Retrieve session from Stripe
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            return {
                "customer_email": session.customer_email,
                "product_id": session.metadata.get("product_id"),
                "payment_status": session.payment_status,
                "subscription_id": session.subscription,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve session: {e}")
            raise

    def process_subscription_created(self, subscription_data: dict) -> Subscription:
        """Process subscription.created webhook.

        Args:
            subscription_data: Subscription data from webhook

        Returns:
            Subscription object
        """
        return Subscription(
            id=subscription_data["id"],
            customer_id=subscription_data["customer"],
            customer_email=subscription_data.get("customer_email", ""),
            product_id=subscription_data["metadata"].get("product_id", ""),
            price_id=subscription_data["items"]["data"][0]["price"]["id"],
            status=SubscriptionStatus(subscription_data["status"]),
            current_period_start=datetime.fromtimestamp(subscription_data["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription_data["current_period_end"]),
            cancel_at_period_end=subscription_data.get("cancel_at_period_end", False),
        )

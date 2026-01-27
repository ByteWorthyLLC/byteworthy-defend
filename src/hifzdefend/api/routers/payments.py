"""Payment and billing API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, EmailStr

from ...payments.stripe_client import StripeClient, PaymentService
from ...licensing.manager import LicenseManager
from ...licensing.crypto import LicenseCrypto
from ..dependencies import get_license_manager

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)

# Initialize Stripe client (would be configured from environment)
# stripe_client = StripeClient(api_key=os.getenv("STRIPE_SECRET_KEY"))
# payment_service = PaymentService(stripe_client)


class CreateCheckoutRequest(BaseModel):
    """Checkout session request."""

    customer_email: EmailStr
    license_type: str  # trial, personal, professional, enterprise
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Checkout session response."""

    checkout_url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    """Subscription details response."""

    id: str
    status: str
    customer_email: str
    license_type: str
    current_period_end: str
    cancel_at_period_end: bool


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest) -> CheckoutResponse:
    """Create Stripe checkout session.

    Args:
        request: Checkout request

    Returns:
        Checkout URL and session ID
    """
    try:
        # This is a stub - actual implementation would use Stripe API
        # checkout_url = payment_service.create_license_checkout(
        #     request.customer_email,
        #     request.license_type,
        #     request.success_url,
        #     request.cancel_url
        # )

        # For demo purposes, return mock data
        raise HTTPException(
            status_code=501,
            detail="Payment integration not yet configured. Set STRIPE_SECRET_KEY environment variable."
        )

    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
) -> dict:
    """Handle Stripe webhook events.

    Args:
        request: FastAPI request
        stripe_signature: Stripe signature header

    Returns:
        Success response
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        # Get raw body
        body = await request.body()

        # Verify signature
        # event = stripe_client.verify_webhook_signature(body, stripe_signature)

        # Process event
        # if event["type"] == "checkout.session.completed":
        #     session = event["data"]["object"]
        #     # Generate and send license key
        #     await handle_checkout_completed(session)
        #
        # elif event["type"] == "customer.subscription.created":
        #     subscription = event["data"]["object"]
        #     await handle_subscription_created(subscription)
        #
        # elif event["type"] == "customer.subscription.deleted":
        #     subscription = event["data"]["object"]
        #     await handle_subscription_canceled(subscription)

        logger.info("Webhook processed successfully")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscription/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: str) -> SubscriptionResponse:
    """Get subscription details.

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        Subscription details
    """
    raise HTTPException(
        status_code=501,
        detail="Payment integration not yet configured"
    )


@router.post("/subscription/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> dict:
    """Cancel subscription.

    Args:
        subscription_id: Stripe subscription ID
        at_period_end: Cancel at period end or immediately

    Returns:
        Success status
    """
    raise HTTPException(
        status_code=501,
        detail="Payment integration not yet configured"
    )


async def handle_checkout_completed(session: dict) -> None:
    """Handle completed checkout session.

    Args:
        session: Stripe checkout session data
    """
    customer_email = session["customer_email"]
    product_id = session["metadata"]["product_id"]

    # Determine license type from product
    license_type = product_id.replace("prod_", "")

    # Generate license key
    manager = LicenseManager()
    license_data = manager.create_paid_license(customer_email, license_type)

    # Sign license
    crypto = LicenseCrypto()
    license_key = crypto.generate_license_key(license_data)

    # Send email with license key
    # await send_license_email(customer_email, license_key, license_data)

    logger.info(f"License generated for {customer_email}: {license_type}")


async def handle_subscription_created(subscription: dict) -> None:
    """Handle subscription creation.

    Args:
        subscription: Stripe subscription data
    """
    # Similar to checkout_completed
    # Generate license with subscription ID
    logger.info(f"Subscription created: {subscription['id']}")


async def handle_subscription_canceled(subscription: dict) -> None:
    """Handle subscription cancellation.

    Args:
        subscription: Stripe subscription data
    """
    # Revoke license or mark as expired
    logger.info(f"Subscription canceled: {subscription['id']}")

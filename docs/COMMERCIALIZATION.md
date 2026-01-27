# HifzDefend Commercialization Guide

This document explains how to configure and use HifzDefend's commercial features for selling licenses.

## Overview

HifzDefend v0.3.0 includes a complete commercialization infrastructure:

- **License Key System**: RSA-based license generation and validation
- **Payment Integration**: Stripe integration for subscriptions and one-time purchases
- **Hardware Binding**: Prevent license sharing across devices
- **Feature Gating**: Control features based on license tier
- **Web Dashboard**: Purchase and license management UI

## Architecture

```
┌─────────────────┐
│   Customer      │
│   Purchases     │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Stripe  │
    │ Checkout│
    └────┬────┘
         │ Webhook
    ┌────▼────────────┐
    │ Payment Handler │
    │  Generate Key   │
    └────┬────────────┘
         │
    ┌────▼────────┐
    │ Email with  │
    │ License Key │
    └────┬────────┘
         │
    ┌────▼────────┐
    │  Customer   │
    │  Activates  │
    └─────────────┘
```

## Setup Instructions

### 1. Generate RSA Keys

Generate public/private key pair for signing licenses:

```bash
# From project root
python scripts/generate_licenses.py keys
```

This creates:
- `src/hifzdefend/licensing/keys/private.pem` (KEEP SECRET!)
- `src/hifzdefend/licensing/keys/public.pem` (embedded in app)

**⚠ WARNING**: Never commit `private.pem` to version control!

### 2. Configure Stripe

#### Create Stripe Account
1. Sign up at https://stripe.com
2. Get your API keys from Dashboard → Developers → API keys

#### Create Products in Stripe Dashboard

**Trial License** (Free)
- Product ID: `prod_trial`
- Price ID: `price_trial`
- Price: $0
- Features: Limited (50 scans/day, 14 days)

**Personal License** ($49/year)
- Product ID: `prod_personal`
- Price ID: `price_personal_annual`
- Price: $4,900 (in cents)
- Billing: Annual subscription
- Features: Full features, 1 device

**Professional License** ($99/year)
- Product ID: `prod_professional`
- Price ID: `price_professional_annual`
- Price: $9,900 (in cents)
- Billing: Annual subscription
- Features: Full features, 3 devices, priority support

**Enterprise License** (Custom)
- Contact sales workflow
- Custom pricing and features

#### Set Environment Variables

```bash
# .env file
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Configure Webhooks

In Stripe Dashboard → Developers → Webhooks:

**Endpoint URL**: `https://your-domain.com/api/v1/payments/webhook`

**Events to listen for**:
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET`.

## Generating Licenses

### Command Line

```bash
# Generate trial license
python scripts/generate_licenses.py trial user@example.com --days 14

# Generate paid license
python scripts/generate_licenses.py paid user@example.com personal --days 365

# Generate perpetual license
python scripts/generate_licenses.py paid user@example.com professional --perpetual
```

### Programmatically

```python
from hifzdefend.licensing.manager import LicenseManager
from hifzdefend.licensing.crypto import LicenseCrypto

# Create license data
license_data = LicenseManager.create_paid_license(
    email="customer@example.com",
    license_type="professional",
    duration_days=365
)

# Sign it
crypto = LicenseCrypto(private_key_path="keys/private.pem")
license_key = crypto.generate_license_key(license_data)

# Format for display
formatted = LicenseCrypto.format_key(license_key)
print(f"License: {formatted}")
```

## License Types

### Trial (Free)
- **Duration**: 14 days
- **Devices**: 1
- **Scans**: 50/day limit
- **Features**: AI analysis, basic real-time protection
- **Support**: Email

### Personal ($49/year)
- **Duration**: Annual subscription
- **Devices**: 1
- **Scans**: Unlimited
- **Features**: Full AI analysis, real-time protection, cloud backup
- **Support**: Priority email

### Professional ($99/year)
- **Duration**: Annual subscription
- **Devices**: 3
- **Scans**: Unlimited
- **Features**: Everything in Personal + API access, custom rules
- **Support**: 24/7 priority

### Enterprise (Custom)
- **Duration**: Negotiable
- **Devices**: 10+
- **Scans**: Unlimited
- **Features**: Everything + on-premise, SLA, custom integrations
- **Support**: Dedicated account manager

## Payment Flow

### Purchase Flow

1. Customer visits `/purchase` page
2. Selects license tier
3. Enters email
4. Redirected to Stripe Checkout
5. Completes payment
6. Stripe sends webhook to `/api/v1/payments/webhook`
7. Backend generates license key
8. License key emailed to customer
9. Redirected to `/license?success=true`

### Activation Flow

1. Customer receives license key via email
2. Opens HifzDefend web dashboard
3. Goes to `/license` page
4. Enters license key
5. Clicks "Activate License"
6. API validates signature and hardware ID
7. License stored locally
8. Features unlocked based on license tier

## Feature Gating

Control features based on license:

```python
from hifzdefend.licensing.manager import LicenseManager

manager = LicenseManager()
license = manager.get_current_license()

if not license:
    # Show trial limitations
    pass

# Check specific features
if license.ai_enabled:
    # Enable AI analysis
    pass

if license.real_time_protection:
    # Enable real-time monitoring
    pass

# Check scan limits
if license.max_scans_per_day:
    # Enforce daily limit
    pass
```

## Webhook Handlers

### checkout.session.completed

```python
async def handle_checkout_completed(session):
    email = session["customer_email"]
    product_id = session["metadata"]["product_id"]
    license_type = product_id.replace("prod_", "")

    # Generate license
    license_data = LicenseManager.create_paid_license(email, license_type)
    license_key = crypto.generate_license_key(license_data)

    # Send email with license key
    await send_license_email(email, license_key)
```

### customer.subscription.deleted

```python
async def handle_subscription_canceled(subscription):
    customer_id = subscription["customer"]

    # Find license by customer_id
    # Mark as expired or revoke
    # Send cancellation email
```

## Security Considerations

### Private Key Security
- Never commit `private.pem` to version control
- Store in secure location (HSM, secret manager in production)
- Rotate keys periodically
- Use environment variables or vault for key path

### Hardware Binding
- Prevents license sharing across devices
- Based on CPU, motherboard serial, MAC address
- Allow hardware changes (e.g., user upgrades computer)
- Provide license transfer mechanism

### License Validation
- Offline validation using public key
- No phone-home required
- RSA signature prevents tampering
- Expiration checking on startup

### Webhook Security
- Always verify webhook signatures
- Use HTTPS for webhook endpoint
- Implement idempotency for webhook handlers
- Log all webhook events for audit

## Testing

### Test Mode

Stripe provides test mode for development:

```bash
# Use test API keys
STRIPE_SECRET_KEY=sk_test_...
```

### Test Cards

```
4242 4242 4242 4242  # Successful payment
4000 0000 0000 0002  # Declined payment
4000 0000 0000 9995  # Insufficient funds
```

### Manual Testing

1. Generate test license:
```bash
python scripts/generate_licenses.py trial test@example.com
```

2. Copy license key from output
3. Open web dashboard at `/license`
4. Paste license key and activate
5. Verify features are unlocked

## Email Integration

Integrate email service to send license keys:

```python
import smtplib
from email.mime.text import MIMEText

async def send_license_email(email: str, license_key: str):
    msg = MIMEText(f"""
    Thank you for purchasing HifzDefend!

    Your license key:
    {LicenseCrypto.format_key(license_key)}

    To activate:
    1. Open HifzDefend
    2. Go to License Management
    3. Enter your license key

    Support: support@hifzdefend.com
    """)

    msg['Subject'] = 'Your HifzDefend License Key'
    msg['From'] = 'noreply@hifzdefend.com'
    msg['To'] = email

    # Send via SMTP
    # ...
```

## Analytics

Track key metrics:

- **License Sales**: Count by type
- **Conversion Rate**: Trial → Paid
- **Churn Rate**: Subscription cancellations
- **Revenue**: MRR, ARR
- **Activation Rate**: Purchases → Activations
- **Support Tickets**: By license type

## Pricing Strategy

### Recommended Pricing

- **Trial**: Free (14 days)
- **Personal**: $49/year ($4.08/month)
- **Professional**: $99/year ($8.25/month)
- **Enterprise**: $500+/year (custom)

### Upsell Opportunities

- Trial → Personal: "Upgrade for unlimited scans"
- Personal → Professional: "Protect 3 devices + priority support"
- Professional → Enterprise: "Custom integrations + SLA"

### Discounts

- Annual vs monthly: 20% off
- Student discount: 50% off Personal
- Nonprofit: Custom pricing
- Volume licensing: Tiered discounts

## Customer Support

### Support Tiers

**Trial/Personal**: Email support (48h response)
**Professional**: Priority email + chat (24h response)
**Enterprise**: Dedicated account manager (4h response)

### Common Issues

1. **License won't activate**: Check internet, hardware changes
2. **Payment failed**: Verify card details, contact bank
3. **Subscription canceled**: Confirm in Stripe dashboard
4. **Need more devices**: Upgrade to Professional/Enterprise

## Roadmap

**Phase 3** (Current): License & Payments ✅
**Phase 4** (Next):
- User authentication and accounts
- Auto-update system
- Usage analytics
- Windows installer

**Phase 5** (Future):
- Reseller/affiliate program
- Volume licensing portal
- Multi-year prepay discounts
- Family plan (5 devices)

## Resources

- [Stripe Documentation](https://stripe.com/docs)
- [License Key Best Practices](https://docs.keygen.sh)
- [SaaS Metrics Guide](https://www.saastr.com/saas-metrics)
- [Pricing Psychology](https://www.priceintelligently.com)

## Support

For questions about commercialization:
- Email: sales@hifzdefend.com
- Docs: https://docs.hifzdefend.com
- Discord: https://discord.gg/hifzdefend

# HifzDefend Customer Portal - PRD

## Overview

Create a web-based customer portal for HifzDefend users to manage their licenses, subscriptions, support tickets, and account settings. This portal is separate from the desktop application's React dashboard and serves as the central customer management interface.

## Goals

- Provide self-service license management
- Enable customers to view purchase history and billing
- Offer support ticket system
- Allow account and subscription management
- Integrate with existing auth, payment, and license systems

## Target Users

- HifzDefend customers (trial, personal, professional, enterprise)
- Sales team (admin interface)
- Support team (ticket management)

## User Stories

### Authentication & Account

**Story 1: User Registration**
As a new customer, I want to create an account so that I can purchase and manage licenses.

Acceptance Criteria:
- Registration form with email, password, full name, company (optional)
- Email validation and confirmation
- Password strength requirements (8+ chars, uppercase, lowercase, digit)
- Terms of service acceptance
- Redirect to dashboard after registration
- Integration with existing auth system

**Story 2: User Login**
As an existing customer, I want to log in to access my account.

Acceptance Criteria:
- Login form with email and password
- "Remember me" option
- "Forgot password" link
- JWT token-based authentication
- Redirect to dashboard after login
- Integration with existing auth API

**Story 3: Password Reset**
As a user, I want to reset my password if I forget it.

Acceptance Criteria:
- Request reset link via email
- Secure reset token generation
- Reset form with password confirmation
- Token expiration (1 hour)
- Success message and redirect to login

### License Management

**Story 4: View Active Licenses**
As a customer, I want to see all my active licenses in one place.

Acceptance Criteria:
- Table showing: license key, type, devices, expiration, status
- Filter by type (trial, personal, professional, enterprise)
- Search by license key
- Color-coded status badges (active, expired, expiring soon)
- Device count per license

**Story 5: Activate New License**
As a customer, I want to activate a license key I purchased.

Acceptance Criteria:
- Input field for license key (formatted XXXXX-XXXXX-XXXXX)
- Real-time validation feedback
- Show license details before activation
- Hardware fingerprint collection
- Activation confirmation with device name
- Integration with license API

**Story 6: Deactivate License from Device**
As a customer, I want to deactivate a license from one device to use it on another.

Acceptance Criteria:
- List of devices where license is active
- Deactivate button per device
- Confirmation dialog with warning
- Update device count in real-time
- Email notification of deactivation

**Story 7: Transfer License**
As a customer, I want to transfer a license to another email address.

Acceptance Criteria:
- Transfer form with destination email
- Email confirmation to both parties
- Original user loses access after transfer
- New user receives activation email
- Transfer logged in audit trail

### Purchase & Billing

**Story 8: Purchase New License**
As a customer, I want to purchase a license from the portal.

Acceptance Criteria:
- Pricing table for all license types
- Stripe Checkout integration
- Redirect to payment page
- License key generation after payment
- Email confirmation with license key
- Redirect to licenses page after success

**Story 9: View Purchase History**
As a customer, I want to see all my past purchases.

Acceptance Criteria:
- Table with: date, license type, amount, status
- Download invoice as PDF
- Filter by date range
- Search by transaction ID
- Show payment method used

**Story 10: Manage Subscription**
As a customer, I want to manage my subscription settings.

Acceptance Criteria:
- Current plan details (price, renewal date, payment method)
- Upgrade/downgrade buttons
- Cancel subscription option with retention flow
- Update payment method
- View next billing date and amount
- Stripe billing portal integration

**Story 11: Apply Discount Code**
As a customer, I want to apply discount codes to purchases.

Acceptance Criteria:
- Discount code input field on purchase page
- Real-time validation
- Show discount amount and final price
- Apply code to Stripe checkout session
- Support: percentage off, fixed amount, trial extension

### Support

**Story 12: Submit Support Ticket**
As a customer, I want to submit support tickets for issues.

Acceptance Criteria:
- Ticket form: subject, description, category, priority
- File attachment support (screenshots, logs)
- Auto-populate license and account info
- Email confirmation of ticket creation
- Ticket ID for tracking

**Story 13: View Support Tickets**
As a customer, I want to view all my support tickets and their status.

Acceptance Criteria:
- Table with: ticket ID, subject, status, priority, created date
- Filter by status (open, in progress, resolved, closed)
- Click ticket to view details and conversation
- Real-time status updates

**Story 14: Respond to Support Ticket**
As a customer, I want to add replies to my open tickets.

Acceptance Criteria:
- Reply text area in ticket detail view
- File attachments on replies
- Email notification to support team
- Conversation thread display
- Timestamp and author for each message

### Dashboard & Analytics

**Story 15: User Dashboard**
As a customer, I want a dashboard showing my account overview.

Acceptance Criteria:
- Active licenses count and status summary
- Next renewal date and amount
- Recent support tickets (last 5)
- Account status badge (trial, active, expired)
- Quick actions: Buy license, Submit ticket, View docs
- Usage statistics if analytics enabled

**Story 16: Usage Analytics**
As a customer, I want to see usage statistics for my licenses.

Acceptance Criteria:
- Scans performed this month (chart)
- Threats detected count
- Device usage breakdown
- AI analysis usage (if enabled)
- Comparison to previous month
- Export data as CSV

### Admin Interface

**Story 17: Admin Dashboard**
As an admin, I want to see system-wide statistics.

Acceptance Criteria:
- Total customers, licenses, revenue
- Active subscriptions count
- Trial conversion rate
- Open support tickets count
- Recent signups and purchases
- Revenue chart (MRR, ARR)

**Story 18: Manage Customer Licenses**
As an admin, I want to manually manage customer licenses.

Acceptance Criteria:
- Search customers by email or license key
- View customer details and license history
- Generate manual license key
- Extend license expiration
- Revoke license with reason
- Audit log of all admin actions

**Story 19: Manage Support Tickets**
As a support agent, I want to respond to customer tickets.

Acceptance Criteria:
- Queue of open tickets sorted by priority
- Assign ticket to agent
- Add internal notes (not visible to customer)
- Change ticket status and priority
- Send reply to customer (email + portal)
- Close ticket with resolution

## Technical Requirements

### Stack
- **Frontend**: Next.js 14+ (React, TypeScript, Tailwind CSS)
- **Backend**: Existing FastAPI (Python) or Next.js API routes
- **Database**: PostgreSQL or existing SQLite (extended schema)
- **Auth**: JWT tokens (existing system)
- **Payments**: Stripe (existing integration)
- **Email**: SendGrid or SES
- **Hosting**: Vercel (frontend) + existing backend deployment

### Security
- HTTPS only
- CSRF protection
- Rate limiting on auth endpoints
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Secure session management

### Performance
- Page load < 2 seconds
- Responsive design (mobile, tablet, desktop)
- Optimistic UI updates
- Lazy loading for tables
- CDN for static assets

### Integration
- Use existing `/api/v1/auth` endpoints
- Use existing `/api/v1/licensing` endpoints
- Use existing `/api/v1/payments` endpoints
- Add new `/api/v1/tickets` endpoints
- Add new `/api/v1/admin` endpoints

## Success Metrics

- 80%+ of license activations self-service (no support contact)
- Support ticket response time < 24 hours
- Customer portal login rate > 50% of customers/month
- Trial → Paid conversion rate > 15%
- Customer satisfaction score > 4.5/5

## Out of Scope

- Mobile app (web only)
- Live chat (tickets only)
- Community forum
- Knowledge base (separate documentation site)
- Reseller/affiliate portal (future)

## Timeline

- Phase 1: Auth + Dashboard + Licenses (2 weeks)
- Phase 2: Purchases + Billing (1 week)
- Phase 3: Support Tickets (1 week)
- Phase 4: Admin Interface (1 week)
- Phase 5: Polish + Testing (1 week)

Total: 6 weeks

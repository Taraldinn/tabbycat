# Extending Tabbycat into a Single Open-Source Platform & Upstream Sync Guide

## Architecture Overview

```mermaid
graph TD
    subgraph Upstream ["Upstream Tabbycat (TabbycatDebate/tabbycat)"]
        U_Core[Core Tabulation Engine]
        U_Draw[Draw & Pairings Generator]
        U_Results[Results & Ballots]
        U_Venues[Venues & Break Calculator]
    end

    subgraph ExtensionLayer ["Modular Enterprise Extension Layer (Non-Invasive)"]
        E_Tenants[tenants: Multi-Tenancy & Host Resolution]
        E_Accounts[accounts: Client Org Portals & Managers]
        E_Billing[billing: Subscriptions & bKash/Nagad Queue]
        E_SuperAdmin[superadmin: Platform Operations Console]
        E_Landing[landing: Branded Homepage & Pricing]
        E_SMS[notifications/sms.py: SMS Dispatch Backend]
    end

    subgraph Infrastructure ["Zero-Redis PostgreSQL Infrastructure"]
        DB_Main[(PostgreSQL Database)]
        DB_Cache[(tabbycat_db_cache Table)]
        ASGI[Daphne ASGI Server]
        Proxy[Caddy / Nginx Reverse Proxy]
    end

    U_Core --> E_Tenants
    ExtensionLayer --> DB_Main
    ExtensionLayer --> DB_Cache
    ASGI --> ExtensionLayer
    Proxy --> ASGI
```

---

## 1. How the Modular Extension Architecture Works

To make sure upstream Tabbycat updates can be merged with zero headaches or merge conflicts, the codebase follows a **Clean Extension Pattern**:

1. **Core Untouched**: Upstream Tabbycat applications (`tournaments`, `participants`, `draw`, `results`, `adjallocation`, `breakqual`) remain structurally independent.
2. **Pluggable Django Apps**: All SaaS and organization features reside in dedicated isolated Django apps:
   - `tabbycat/tenants/`: Middleware for resolving `request.tenant` from subdomains (`<slug>.tabbycatbd.com`) or custom domains (`debates.nsudc.org`).
   - `tabbycat/accounts/`: Onboarding registration, organization profile management, site manager assignments, custom domain configuration, and user timezone settings.
   - `tabbycat/billing/`: Subscription plans, limits enforcement, invoice history, and manual bKash/Nagad/Rocket payment queue.
   - `tabbycat/superadmin/`: Platform-wide governance, payment verification, user password reset dispatching, and system metrics.
   - `tabbycat/landing/`: Dynamic landing page, features showcase, and responsive pricing tables.
   - `tabbycat/notifications/sms.py`: Extensible SMS notification provider with pluggable backends (Greenweb, SSL Wireless, Webhooks, Console).
3. **Database Caching (Zero Redis)**:
   - Django `DatabaseCache` backend stores session and cache keys in PostgreSQL table `tabbycat_db_cache`.
   - Django Channels uses in-memory layer (`InMemoryChannelLayer`) or PostgreSQL, enabling full deployment without a Redis container.

---

## 2. Upstream Synchronization Workflow (Zero Complexity Merges)

To sync your repository with new features, bug fixes, or security patches from official upstream Tabbycat:

```mermaid
gitGraph
    commit id: "Upstream v2.11.0"
    branch saas-platform
    checkout saas-platform
    commit id: "Add Multi-tenancy"
    commit id: "Add PostgreSQL Caching"
    commit id: "Add Space Grotesk UI"
    checkout main
    commit id: "Upstream v2.12.0"
    checkout saas-platform
    merge main id: "Sync upstream (git merge upstream/master)"
    commit id: "All SaaS features preserved"
```

### Step-by-Step Git Commands:

1. **Add Upstream Remote** (One-time setup):
   ```bash
   git remote add upstream https://github.com/TabbycatDebate/tabbycat.git
   git fetch upstream
   ```

2. **Fetch and Merge Upstream Updates**:
   ```bash
   # Switch to your development or main branch
   git checkout master

   # Fetch latest changes from upstream Tabbycat
   git fetch upstream master

   # Merge upstream changes into your branch
   git merge upstream/master
   ```

3. **Run Migrations & Tests**:
   ```bash
   # Run Django database migrations
   python manage.py migrate

   # Collect static assets
   python manage.py collectstatic --no-input

   # Run automated test suite
   python manage.py test accounts.tests billing.tests superadmin.tests tenants.tests landing.tests notifications.tests --noinput
   ```

Because your custom logic lives in dedicated apps (`tenants`, `accounts`, `billing`, `superadmin`, `landing`), upstream merges will apply cleanly to the core tab engine without conflict.

---

## 3. Production Deployment Guide (Single-Server / Docker)

### Option A: Standard Single-Server (Systemd + Caddy + PostgreSQL)

1. **System Architecture**:
   - Web Server: **Caddy** (Handles automated TLS for wildcard `*.tabbycatbd.com` and on-demand custom domains).
   - Application Server: **Daphne ASGI** running under `systemd` on port `8000`.
   - Database & Cache: **PostgreSQL 14+** (main database + cache table).

2. **Caddyfile Configuration (`/etc/caddy/Caddyfile`)**:
   ```caddy
   # Wildcard and Root Subdomains
   *.tabbycatbd.com, tabbycatbd.com {
       tls {
           dns cloudflare {$CLOUDFLARE_API_TOKEN}
       }
       reverse_proxy 127.0.0.1:8000 {
           header_up Host {host}
           header_up X-Real-IP {remote}
           header_up X-Forwarded-Proto {scheme}
       }
   }

   # Automated On-Demand TLS for Client Custom Domains (e.g. debates.nsudc.org)
   :443 {
       tls {
           on_demand
       }
       reverse_proxy 127.0.0.1:8000 {
           header_up Host {host}
           header_up X-Real-IP {remote}
           header_up X-Forwarded-Proto {scheme}
       }
   }
   ```

3. **Environment Variables (`.env`)**:
   ```env
   DJANGO_SETTINGS_MODULE=tabbycat.settings.production
   DATABASE_URL=postgresql://tabbycat_user:secure_password@127.0.0.1:5432/tabbycat
   TABBYCAT_BASE_DOMAIN=tabbycatbd.com
   TABBYCAT_SMS_BACKEND=greenweb
   TABBYCAT_SMS_API_KEY=your_greenweb_api_token
   TABBYCAT_SMS_SENDER_ID=TABBYCAT
   TABBYCAT_CACHE_BACKEND=database
   ```

---

## 4. How to Extend New Features

### Adding a New Payment Gateway (e.g. Stripe or SSLCommerz):
1. Navigate to [`tabbycat/billing/views.py`](file:///home/taraldinn/Documents/tabbycat/tabbycat/billing/views.py).
2. Create a webhook endpoint (e.g. `StripeWebhookView`).
3. In the webhook handler, query `Payment.objects.get(transaction_id=...)`, update status to `Payment.Status.VERIFIED`, and call `payment.sync_tenant_subscription()`.

### Adding a New SMS Provider:
1. Open [`tabbycat/notifications/sms.py`](file:///home/taraldinn/Documents/tabbycat/tabbycat/notifications/sms.py).
2. Subclass `BaseSMSBackend` and implement `send_sms(self, to_number, message_text)`:
   ```python
   class TwilioSMSBackend(BaseSMSBackend):
       def send_sms(self, to_number, message_text):
           # Twilio API dispatch logic here
           return True
   ```
3. Register the backend in `get_sms_backend()`.

---

## 5. Summary & Best Practices
- **Never touch core Tabbycat migrations**: Keep custom tenant schema in `tenants.0001_initial` or subsequent migrations.
- **Run automated test suite before every release**:
  ```bash
  python manage.py test accounts.tests billing.tests superadmin.tests tenants.tests landing.tests notifications.tests --noinput
  ```
- **Leverage PostgreSQL Database Cache**: Always execute `python manage.py createcachetable` if initializing on a fresh PostgreSQL instance.

# RISKCORE Security Architecture

> Last Updated: 2026-01-10
> Status: Strategic Planning
> Author: Massimo Todaro / Claude

---

## Executive Summary

RISKCORE is a **READ-ONLY risk aggregation platform**. We never write back to source systems, never execute trades, and never modify client booking data. This fundamentally shapes our security posture:

**What we ARE:**
- A viewing and analytics platform
- A data processor (clients are data controllers)
- A read-only overlay on existing systems

**What we are NOT:**
- A trading platform (no risky actions can go through us)
- An order management system
- A data controller for position/trade data

This document covers authentication, authorization, data protection, GDPR compliance, and audit requirements.

---

## Table of Contents

1. [Core Security Principles](#1-core-security-principles)
2. [Authentication](#2-authentication)
3. [Authorization & Role-Based Access Control](#3-authorization--role-based-access-control)
4. [Data Protection](#4-data-protection)
5. [GDPR & Data Residency](#5-gdpr--data-residency)
6. [Audit Logging](#6-audit-logging)
7. [Export Controls](#7-export-controls)
8. [API Security](#8-api-security)
9. [Infrastructure Security](#9-infrastructure-security)
10. [Incident Response](#10-incident-response)
11. [Compliance Roadmap](#11-compliance-roadmap)
12. [Future: Treasury Risk Module](#12-future-treasury-risk-module)

---

## 1. Core Security Principles

### 1.1 Defense in Depth

Multiple layers of security:
```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: NETWORK                         │
│            HTTPS everywhere, API rate limiting              │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 2: AUTHENTICATION                  │
│     Supabase Auth, JWT tokens, 2FA (Enterprise)            │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 3: AUTHORIZATION                   │
│     Row Level Security, Role-based permissions              │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 4: DATA PROTECTION                 │
│     Encryption at rest, encryption in transit               │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 5: AUDIT                           │
│     Sensitive action logging, immutable audit trail         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Principle of Least Privilege

- Users get minimum permissions required for their role
- PMs see only their own book(s)
- Analysts see only assigned books
- No user can access another tenant's data

### 1.3 Read-Only by Design

- RISKCORE never writes back to source systems
- We cannot modify booking system data
- No trade execution capability
- Risk mitigation: even if compromised, no financial damage to client portfolios

---

## 2. Authentication

### 2.1 Authentication Methods by Tier

| Tier | Method | 2FA | SSO |
|------|--------|-----|-----|
| **Free** | Email + Password | ❌ | ❌ |
| **Pro** | Email + Password | Optional | ❌ |
| **Enterprise** | Email + Password | ✅ Required | ✅ Available |

### 2.2 Implementation

**Provider:** Supabase Auth

**Features:**
- JWT-based session management
- Secure password hashing (bcrypt)
- Email verification on signup
- Password reset flow
- Session expiry (configurable, default 7 days)

### 2.3 Two-Factor Authentication (2FA)

**Availability:** Enterprise tier only

**Supported Methods:**
- TOTP (Google Authenticator, Authy, etc.)
- SMS backup (optional)

**Implementation:** Supabase Auth MFA

```sql
-- User table extension for 2FA
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN mfa_secret TEXT; -- Encrypted TOTP secret
```

### 2.4 SSO / SAML (Enterprise)

**Status:** Nice-to-have, Phase 2-3

**Planned Support:**
- SAML 2.0
- OAuth 2.0 / OpenID Connect
- Azure AD
- Okta
- Google Workspace

**Implementation:** Third-party provider (WorkOS, Auth0) or Supabase Enterprise

---

## 3. Authorization & Role-Based Access Control

### 3.1 Role Hierarchy

```
SUPERADMIN (RISKCORE Team)
    │
    └── ADMIN (Firm Admin)
            │
            ├── CIO/CEO (All books, view-only)
            │
            ├── CRO (All books, can set limits)
            │
            ├── PM (Own book(s) only)
            │
            └── ANALYST (Assigned books, view-only)
```

### 3.2 Permission Matrix

| Action | SuperAdmin | Admin | CIO/CEO | CRO | PM | Analyst |
|--------|------------|-------|---------|-----|-----|---------|
| View all tenants | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create tenant | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View all books | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| View own book(s) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Set risk limits | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Override model inputs | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Export trades | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Export Riskboard | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Export correlation | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Export PM drill-down | ✅ | ✅ | ✅ | ✅ | Own only | ❌ |
| API access | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Upload data | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Configure integrations | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

### 3.3 Row Level Security (RLS)

**Implementation:** Supabase PostgreSQL RLS

```sql
-- Enable RLS on all tables
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE books ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy
CREATE POLICY tenant_isolation ON positions
    FOR ALL
    USING (tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid()));

-- Book access policy
CREATE POLICY book_access ON positions
    FOR SELECT
    USING (
        book_id IN (
            SELECT book_id FROM user_book_access WHERE user_id = auth.uid()
        )
        OR
        (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'cio', 'cro')
    );
```

### 3.4 JWT Claims Structure

```json
{
  "sub": "user-uuid",
  "email": "user@firm.com",
  "tenant_id": "tenant-uuid",
  "role": "pm",
  "book_ids": ["book-1-uuid", "book-2-uuid"],
  "plan": "pro",
  "mfa_verified": true,
  "exp": 1704931200
}
```

---

## 4. Data Protection

### 4.1 Encryption

| Layer | Method | Provider |
|-------|--------|----------|
| **In Transit** | TLS 1.3 | Supabase / Cloudflare |
| **At Rest** | AES-256 | Supabase (PostgreSQL) |
| **Backups** | AES-256 | Supabase |

### 4.2 Data Classification

| Classification | Examples | Handling |
|----------------|----------|----------|
| **Public** | Marketing content | No restrictions |
| **Internal** | Aggregated analytics | Tenant-isolated |
| **Confidential** | Position data, risk metrics | RLS, encryption |
| **Restricted** | User credentials, API keys | Encrypted, never logged |

### 4.3 Data Retention

**Policy:** 5 years, not configurable

| Data Type | Retention |
|-----------|-----------|
| Position snapshots | 5 years |
| Trade history | 5 years |
| Risk metrics | 5 years |
| Audit logs | 5 years |
| User sessions | 30 days |
| Temporary files | 24 hours |

**Rationale:** Financial regulations typically require 5-7 year retention. Fixed policy simplifies compliance.

### 4.4 Data Deletion

On account termination:
1. User requests deletion via Admin
2. 30-day grace period (recoverable)
3. Permanent deletion after grace period
4. Audit log retained (anonymized)

**Note:** Data may be retained longer if required by law (e.g., regulatory investigation).

---

## 5. GDPR & Data Residency

### 5.1 RISKCORE's GDPR Status

**Role:** Data Processor

**Why?** RISKCORE processes data on behalf of clients (Data Controllers). We do not determine the purpose of data collection — clients do.

**Client Role:** Data Controller

**Relationship:**
```
Client (Hedge Fund) → Data Controller
         ↓ instructs
RISKCORE → Data Processor
         ↓ uses
Supabase → Sub-processor
```

### 5.2 What Data We Process

| Data Type | Personal Data? | GDPR Applies? |
|-----------|----------------|---------------|
| Position data (ticker, quantity, price) | ❌ No | ❌ No |
| Trade records (symbol, size, execution) | ❌ No | ❌ No |
| Risk metrics (VaR, Greeks, exposures) | ❌ No | ❌ No |
| PM names | ⚠️ Potentially | ✅ If identifiable |
| User accounts (email, login) | ✅ Yes | ✅ Yes |
| Audit logs (who did what) | ✅ Yes | ✅ Yes |

**Key Insight:** Most RISKCORE data (positions, trades, risk metrics) is NOT personal data. GDPR primarily applies to user account data.

### 5.3 GDPR Does NOT Require EU Data Residency

From research:

> "GDPR does not mandate that data must physically reside within the European Union. However, it does heavily regulate any transfer of personal data to countries outside the EEA."

**Legal Mechanisms for US Data Storage:**
1. **EU-US Data Privacy Framework** — Adequacy decision for certified US companies
2. **Standard Contractual Clauses (SCCs)** — Contractual safeguards
3. **Binding Corporate Rules** — For corporate groups

### 5.4 RISKCORE Data Residency Approach

**MVP / Pro Tier:**
- US infrastructure (Supabase, AWS us-east)
- Adequate for most clients
- SCCs and DPA template provided

**Enterprise Tier (Phase 2-3):**
- EU region option (Supabase EU, AWS eu-west)
- Required for some European clients
- IP whitelisting available

### 5.5 Data Processing Agreement (DPA)

Required for all clients processing EU data. Template includes:

- Nature and purpose of processing
- Types of personal data processed
- Duration of processing
- Sub-processors list (Supabase, etc.)
- Security measures
- Breach notification procedures
- Data subject rights procedures

### 5.6 Client Responsibilities (Data Controller)

Clients are responsible for:
- Lawful basis for collecting position/trade data
- Informing their employees (PMs, traders) about data processing
- Responding to data subject requests
- Notifying RISKCORE of any data subject requests

### 5.7 RISKCORE Responsibilities (Data Processor)

RISKCORE is responsible for:
- Processing data only as instructed by client
- Implementing appropriate security measures
- Assisting client with data subject requests
- Notifying client of data breaches within 72 hours
- Maintaining records of processing activities
- Providing DPA to all clients

---

## 6. Audit Logging

### 6.1 Philosophy

**Sensitive actions only** (start simple, expand later)

**Rationale:** We are a viewing platform, not a trading platform. No risky actions can go through us. We focus on logging:
- Authentication events
- Authorization changes
- Data exports
- Configuration changes
- Limit breaches

### 6.2 Logged Actions

| Category | Actions Logged |
|----------|----------------|
| **Authentication** | Login success, login failure, logout, password change, 2FA enable/disable |
| **Authorization** | Role change, book access grant/revoke, user create/delete |
| **Data Export** | Any export (Riskboard, correlation, drill-down) |
| **Configuration** | Risk limit create/update/delete, integration add/remove, model override |
| **Limit Events** | Limit breach, limit clear |
| **System** | API key create/revoke, tenant create, plan change |

### 6.3 Audit Log Schema

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),  -- NULL for system events
    action VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,  -- Additional context
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for efficient querying
CREATE INDEX idx_audit_tenant_date ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

### 6.4 Example Audit Entries

```json
{
  "action": "USER_LOGIN_SUCCESS",
  "category": "authentication",
  "details": {
    "method": "password",
    "mfa_used": true
  }
}

{
  "action": "EXPORT_RISKBOARD",
  "category": "data_export",
  "resource_type": "riskboard",
  "details": {
    "format": "csv",
    "books_included": ["book-1", "book-2"],
    "as_of_date": "2026-01-10"
  }
}

{
  "action": "LIMIT_BREACH",
  "category": "limit_events",
  "resource_type": "risk_limit",
  "resource_id": "limit-uuid",
  "details": {
    "limit_type": "hard",
    "risk_factor": "equity_beta",
    "limit_value": 5000000,
    "actual_value": 5234000,
    "breach_pct": 4.68
  }
}
```

### 6.5 Audit Log Retention

- Retention: 5 years
- Storage: Immutable (append-only)
- Access: SuperAdmin and Admin (own tenant only)
- Export: SuperAdmin only

### 6.6 Future Expansion

Potential future logging (not MVP):
- Page views / feature usage (for analytics)
- Search queries
- Correlation matrix views
- Every API call (for debugging)

---

## 7. Export Controls

### 7.1 Export Permission Matrix

| Export Type | SuperAdmin | Admin | CIO/CEO | CRO | PM | Analyst |
|-------------|------------|-------|---------|-----|-----|---------|
| **Underlying Trades** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Riskboard (aggregated)** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Correlation Matrix** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **PM Drill-down** | ✅ | ✅ | ✅ | ✅ | Own book | ❌ |

### 7.2 Rationale

**Underlying Trades — SuperAdmin Only:**
- Raw source data from client booking systems
- Most sensitive data in the platform
- Exporting could expose proprietary trading strategies
- Only RISKCORE team needs this for debugging/support

**Riskboard — Admin, CIO, CRO:**
- Aggregated exposure data
- CROs need to share risk reports with boards and regulators
- Already abstracted from individual trades

**Correlation Matrix — Admin, CIO, CRO:**
- Analytical output, not raw data
- Useful for board presentations
- No trade-level detail

**PM Drill-down — CRO + PM (own book only):**
- More sensitive than Riskboard (shows book-level detail)
- PMs should be able to export their own book's risk
- CRO needs access to all books for oversight
- Analysts can view but not export

### 7.3 Export Formats

| Format | Use Case |
|--------|----------|
| CSV | Spreadsheet analysis |
| PDF | Board reports, regulatory filings |
| JSON | API consumers (Enterprise) |

### 7.4 Export Watermarking

All exports include:
- Timestamp
- User who exported
- Tenant name
- "Confidential — [Tenant Name]" watermark (PDF)

---

## 8. API Security

### 8.1 API Access

**Availability:** Admin role only

| Tier | API Access | Rate Limit |
|------|------------|------------|
| Free | ❌ | N/A |
| Pro | ✅ | 100 requests/minute |
| Enterprise | ✅ | 1000 requests/minute |

### 8.2 Authentication

**Method:** API Key + JWT

```bash
# API request example
curl -X GET https://api.riskcore.io/v1/riskboard \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-API-Key: <api_key>"
```

### 8.3 API Key Management

- Keys created/revoked by Admin
- Keys are hashed in database (never stored in plain text)
- Each key has:
  - Name/description
  - Expiry date (optional)
  - Last used timestamp
  - IP whitelist (Enterprise)

### 8.4 Rate Limiting

**Implementation:** FastAPI middleware

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/v1/riskboard")
@limiter.limit("100/minute")  # Pro tier
async def get_riskboard():
    ...
```

### 8.5 Input Validation

**Implementation:** Pydantic models

- All inputs validated before processing
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding
- File upload validation (type, size)

---

## 9. Infrastructure Security

### 9.1 Supabase Security (Built-in)

| Feature | Status |
|---------|--------|
| Row Level Security (RLS) | ✅ Enabled |
| SSL/TLS encryption | ✅ Default |
| Database encryption at rest | ✅ Default |
| Automatic backups | ✅ Daily |
| DDoS protection | ✅ Cloudflare |
| SOC 2 Type II | ✅ Supabase certified |

### 9.2 Additional Security Measures

**HTTPS Everywhere:**
- All traffic encrypted via TLS 1.3
- HSTS enabled
- Certificate managed by Cloudflare/Vercel

**Secrets Management:**
- Environment variables for all secrets
- Never commit secrets to code
- Rotate API keys annually
- Use `.env.local` for development (gitignored)

**Dependency Security:**
- Dependabot enabled for vulnerability scanning
- Monthly dependency updates
- No known critical vulnerabilities policy

---

## 10. Incident Response

### 10.1 Incident Classification

| Severity | Definition | Response Time |
|----------|------------|---------------|
| **Critical** | Data breach, system compromise | Immediate (< 1 hour) |
| **High** | Service outage, security vulnerability | < 4 hours |
| **Medium** | Performance degradation, minor bugs | < 24 hours |
| **Low** | Feature requests, minor issues | < 1 week |

### 10.2 Data Breach Procedure

1. **Detect:** Automated monitoring or user report
2. **Contain:** Isolate affected systems
3. **Assess:** Determine scope and impact
4. **Notify:**
   - Internal team: Immediately
   - Affected clients: Within 72 hours (GDPR requirement)
   - Regulators: Within 72 hours if required
5. **Remediate:** Fix vulnerability, restore systems
6. **Review:** Post-incident analysis, update procedures

### 10.3 Contact Information

- Security issues: security@riskcore.io
- General support: support@riskcore.io
- Emergency (Enterprise): Dedicated Slack channel

---

## 11. Compliance Roadmap

### 11.1 MVP (Launch)

| Requirement | Status |
|-------------|--------|
| HTTPS everywhere | ✅ |
| RLS tenant isolation | ✅ |
| Input validation | ✅ |
| Audit logging (sensitive) | ✅ |
| Password security | ✅ |
| DPA template | ✅ |

### 11.2 Phase 2 (6-12 months)

| Requirement | Status |
|-------------|--------|
| 2FA (Enterprise) | 🔄 Planned |
| SSO/SAML | 🔄 Planned |
| EU data residency option | 🔄 Planned |
| IP whitelisting | 🔄 Planned |
| SOC 2 Type II audit | 🔄 Planned |

### 11.3 Phase 3 (12-24 months)

| Requirement | Status |
|-------------|--------|
| ISO 27001 certification | 🔄 Planned |
| Penetration testing | 🔄 Planned |
| Dedicated infrastructure (Enterprise) | 🔄 Planned |
| Custom data retention policies | 🔄 Planned |

---

## 12. Future: Treasury Risk Module

### 12.1 Overview

Future module for capital risk, regulatory capital, and liquidity risk:

| Feature | Description |
|---------|-------------|
| **Basel III/IV** | Capital adequacy calculations |
| **RWA** | Risk-Weighted Assets calculation |
| **LCR** | Liquidity Coverage Ratio |
| **NSFR** | Net Stable Funding Ratio |
| **Leverage Ratio** | Tier 1 capital / total exposure |
| **Capital Buffers** | CCB, CCyB, G-SIB buffers |

### 12.2 Security Implications

Treasury Risk module will require:
- Stricter access controls (regulatory data)
- Enhanced audit logging
- Regulatory reporting exports (restricted)
- Potential data residency requirements (jurisdiction-specific)

### 12.3 Additional Roles (Future)

| Role | Permissions |
|------|-------------|
| **Treasury** | View treasury metrics, export regulatory reports |
| **Compliance** | View all risk, generate compliance reports |
| **Regulator** | Read-only access to specific reports (via secure portal) |

---

## Appendix A: Free Tier Branding

### A.1 "Powered by RISKCORE" Watermark

**Placement:** Bottom-right corner of dashboard

**Style:**
- Small, subtle, non-intrusive
- Light gray text on light background
- Does not obstruct any functionality
- Tasteful, professional

**Implementation:**
```jsx
// Free tier only
{plan === 'free' && (
  <div className="fixed bottom-4 right-4 text-xs text-gray-400 opacity-60">
    Powered by RISKCORE
  </div>
)}
```

**Removal:** Upgrading to Pro tier removes the watermark.

---

## Appendix B: Security Checklist

### B.1 Pre-Launch Checklist

- [ ] All secrets in environment variables
- [ ] RLS enabled on all tables
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] HTTPS enforced
- [ ] Audit logging active
- [ ] Backup system tested
- [ ] DPA template ready
- [ ] Privacy policy published
- [ ] Security contact published

### B.2 Ongoing Security Tasks

| Task | Frequency |
|------|-----------|
| Dependency updates | Monthly |
| Access review | Quarterly |
| Backup restoration test | Quarterly |
| Security training | Annually |
| Penetration test | Annually (Phase 2+) |
| SOC 2 audit | Annually (Phase 2+) |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Claude | Initial version |

---

*Security architecture for RISKCORE platform*

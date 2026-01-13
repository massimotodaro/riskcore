# RISKCORE Compliance Architecture

> Building compliant from day 1 - certification when revenue supports it

---

## Executive Summary

RISKCORE is designed as a **self-hosted, on-premises, read-only** risk analytics platform. This architecture fundamentally changes our compliance posture:

| Aspect | RISKCORE Reality | Compliance Impact |
|--------|------------------|-------------------|
| **Data Location** | Client's infrastructure | Client is Data Controller |
| **Data Ownership** | Client owns all data | We are Data Processor (minimal) |
| **Network Access** | Air-gapped option available | Reduced attack surface |
| **Data Transmission** | No data leaves client network | No cross-border transfer issues |
| **SaaS Model** | Self-hosted, not cloud SaaS | Different compliance requirements |

**Strategy:** Build following all SOC 2 and GDPR principles from day 1. Pursue formal certification when revenue supports it (post $500K ARR).

---

## RISKCORE's Unique Position

### What RISKCORE Is

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RISKCORE DEPLOYMENT MODEL                             │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    CLIENT'S INFRASTRUCTURE                           │   │
│   │                    (On-Premises / Private Cloud)                     │   │
│   │                                                                      │   │
│   │   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │   │
│   │   │   RISKCORE      │    │   PostgreSQL    │    │   Client's      │ │   │
│   │   │   Application   │◄───│   Database      │◄───│   Data Sources  │ │   │
│   │   │   (Read-Only)   │    │   (Client-owned)│    │   (Bloomberg,   │ │   │
│   │   └─────────────────┘    └─────────────────┘    │   Enfusion etc) │ │   │
│   │                                                  └─────────────────┘ │   │
│   │                                                                      │   │
│   │   ════════════════════════════════════════════════════════════════   │   │
│   │              ALL DATA STAYS WITHIN CLIENT'S NETWORK                  │   │
│   │   ════════════════════════════════════════════════════════════════   │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    INTERNET / CLOUD                                  │   │
│   │                                                                      │   │
│   │   ┌─────────────────┐    ┌─────────────────┐                        │   │
│   │   │   License       │    │   Documentation │    NO POSITION/TRADE   │   │
│   │   │   Validation    │    │   & Updates     │    DATA TRANSMITTED    │   │
│   │   │   (Optional)    │    │   (GitHub)      │                        │   │
│   │   └─────────────────┘    └─────────────────┘                        │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What RISKCORE Is NOT

| We Are NOT | Why It Matters |
|------------|----------------|
| A cloud SaaS storing client data | No data residency concerns |
| A trading platform | No execution risk, read-only |
| A data controller | Clients control their own data |
| An OMS/EMS | No trade lifecycle management |
| A custodian | No asset custody |

---

## SOC 2 Trust Services Criteria - Built Into RISKCORE

We implement all 5 Trust Services Criteria in our architecture, even without formal certification.

### 1. Security (Required)

**Protection against unauthorized access**

| Control | Implementation | Status |
|---------|----------------|--------|
| **Access Control** | RBAC with 6 roles (SuperAdmin, Admin, CIO, CRO, PM, Analyst) | ✅ Built |
| **Authentication** | JWT-based auth, password hashing (bcrypt) | ✅ Built |
| **MFA Support** | TOTP-based MFA (Pro/Enterprise tiers) | 🔄 Planned |
| **Encryption at Rest** | PostgreSQL TDE (client configures) | ✅ Documented |
| **Encryption in Transit** | TLS 1.3 required | ✅ Built |
| **Session Management** | Configurable timeout, token expiry | ✅ Built |
| **Audit Logging** | All sensitive actions logged | ✅ Built |
| **Input Validation** | Pydantic models, SQL parameterization | ✅ Built |
| **Rate Limiting** | FastAPI middleware, configurable limits | ✅ Built |

**Row Level Security (RLS)**
```sql
-- Every table has tenant isolation
CREATE POLICY tenant_isolation ON positions
    FOR ALL
    USING (tenant_id = current_tenant_id());

-- Book-level access control
CREATE POLICY book_access ON positions
    FOR SELECT
    USING (
        book_id IN (SELECT book_id FROM user_book_access WHERE user_id = current_user_id())
        OR current_user_role() IN ('admin', 'cio', 'cro')
    );
```

### 2. Availability

**System availability for operation**

| Control | Implementation | Status |
|---------|----------------|--------|
| **Uptime Monitoring** | Health check endpoints | ✅ Built |
| **Graceful Degradation** | Fallback for external services | ✅ Built |
| **Database Backups** | Client responsibility (documented) | 📄 Documented |
| **Recovery Procedures** | Documented in deployment guide | 📄 Documented |
| **Capacity Planning** | Performance guidelines provided | 📄 Documented |

**Note:** Since RISKCORE is self-hosted, availability is primarily the client's responsibility. We provide:
- Health check endpoints
- Performance tuning guidelines
- Backup/recovery documentation
- Resource requirement specifications

### 3. Processing Integrity

**System processing is complete, accurate, and timely**

| Control | Implementation | Status |
|---------|----------------|--------|
| **Data Validation** | 11-rule validation pipeline | ✅ Built |
| **Input Sanitization** | Pydantic models, type checking | ✅ Built |
| **Calculation Verification** | Unit tests for all risk calculations | ✅ Built |
| **Audit Trail** | Position changes tracked | ✅ Built |
| **Error Handling** | Comprehensive error responses | ✅ Built |
| **Data Reconciliation** | Reconciliation reports | 🔄 Planned |

**Validation Pipeline**
```python
VALIDATION_RULES = [
    "required_fields",      # All mandatory fields present
    "data_types",           # Correct types (numeric, date, etc.)
    "value_ranges",         # Quantity > 0, price > 0, etc.
    "referential_integrity",# Book exists, security exists
    "business_rules",       # Asset class valid, currency valid
    "duplicate_detection",  # No duplicate positions
    "stale_data",          # Price freshness checks
    "cross_field",         # Option expiry > trade date
    "format",              # ISIN format, CUSIP format
    "consistency",         # Long/short matches quantity sign
    "completeness"         # All required identifiers present
]
```

### 4. Confidentiality

**Information designated as confidential is protected**

| Control | Implementation | Status |
|---------|----------------|--------|
| **Data Classification** | 4 levels defined | ✅ Defined |
| **Multi-Tenant Isolation** | tenant_id + RLS on all tables | ✅ Built |
| **Export Controls** | Role-based export permissions | ✅ Built |
| **No Data Transmission** | All data stays on-premises | ✅ Architecture |
| **Secrets Management** | Environment variables, no hardcoding | ✅ Built |

**Data Classification Levels**
| Level | Examples | Controls |
|-------|----------|----------|
| **Public** | Marketing, documentation | None |
| **Internal** | Aggregated analytics | Tenant isolation |
| **Confidential** | Positions, trades, risk | RLS + encryption |
| **Restricted** | API keys, credentials | Encrypted + never logged |

### 5. Privacy

**Personal information handling**

| Control | Implementation | Status |
|---------|----------------|--------|
| **Minimal PII Collection** | Only user accounts (email, name) | ✅ By design |
| **No Position PII** | Positions/trades are not personal data | ✅ Architecture |
| **Data Subject Rights** | Delete account, export data | 🔄 Planned |
| **Consent Management** | Terms acceptance on signup | 🔄 Planned |
| **Privacy Policy** | Published and accessible | 📄 Planned |

**Privacy by Design**
- RISKCORE processes financial data (positions, trades), NOT personal data
- The only PII we handle: user email, name for authentication
- PM names in books could be considered PII - pseudonymization available

---

## GDPR Compliance Analysis

### RISKCORE's GDPR Status

**Critical Distinction:** RISKCORE's self-hosted architecture fundamentally changes GDPR applicability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GDPR ROLES                                          │
│                                                                              │
│   TRADITIONAL SAAS                    RISKCORE (SELF-HOSTED)                │
│   ─────────────────                   ──────────────────────                │
│                                                                              │
│   SaaS Vendor                         Client (Hedge Fund)                   │
│   = Data Processor                    = Data Controller                     │
│   (holds client data)                 = Data Processor                      │
│                                       (processes their own data)            │
│         │                                                                    │
│         ▼                             RISKCORE                               │
│   Sub-processors                      = Software Provider                   │
│   (AWS, etc.)                         = NOT a Data Processor               │
│                                       (no access to client data)            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### GDPR Applicability to RISKCORE

| Data Type | Location | GDPR Applies? | Controller |
|-----------|----------|---------------|------------|
| Position data | Client's servers | To client, not RISKCORE | Client |
| Trade records | Client's servers | To client, not RISKCORE | Client |
| Risk metrics | Client's servers | To client, not RISKCORE | Client |
| User accounts (email) | Client's servers | To client | Client |
| License validation | Our servers | Yes, to us | RISKCORE |
| Support tickets | Our systems | Yes, to us | RISKCORE |

### What RISKCORE Must Do for GDPR

**For Our Own Systems (license, support, marketing):**

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Legal basis for processing | Legitimate interest, consent | 📄 Planned |
| Privacy policy | Website, clear language | 📄 Planned |
| Data subject rights | Account deletion, data export | 🔄 Planned |
| Breach notification | 72-hour notification process | 📄 Planned |
| Records of processing | Processing activities log | 📄 Planned |
| DPO appointment | Not required (< 250 employees) | N/A |

**For Client Deployments:**

| Client Responsibility | RISKCORE Support |
|----------------------|------------------|
| Data protection impact assessment | Template provided |
| Lawful basis for processing | Guidance documentation |
| Data subject access requests | Export functionality |
| Right to erasure | Delete functionality |
| Data breach response | Incident response template |

### GDPR Data Processing Agreement (DPA)

**When Required:** Only if RISKCORE has access to client data (support, debugging)

**Standard Clauses:**
1. RISKCORE processes data only on client instructions
2. RISKCORE implements appropriate security measures
3. RISKCORE assists with data subject requests
4. RISKCORE notifies client of breaches within 72 hours
5. RISKCORE deletes data after engagement ends

**For Self-Hosted (No Access):** DPA may not be required since we never access client data.

---

## Privacy Regulations Beyond GDPR

### Global Privacy Landscape

| Regulation | Jurisdiction | Applicability to RISKCORE |
|------------|--------------|---------------------------|
| **GDPR** | EU/EEA | License system, support only |
| **CCPA/CPRA** | California | If CA users (license system) |
| **UK GDPR** | United Kingdom | UK customers |
| **LGPD** | Brazil | Brazilian customers |
| **POPIA** | South Africa | SA customers |
| **PDPA** | Singapore | Singapore customers |
| **Privacy Act** | Australia | Australian customers |

### Key Privacy Principles (Universal)

All major privacy laws share these principles:

| Principle | RISKCORE Implementation |
|-----------|------------------------|
| **Lawfulness** | Clear terms, consent where needed |
| **Purpose Limitation** | Only process for stated purposes |
| **Data Minimization** | Collect only what's necessary |
| **Accuracy** | Allow users to update data |
| **Storage Limitation** | Defined retention periods |
| **Security** | Encryption, access controls |
| **Accountability** | Documentation, audit trails |

---

## Financial Services Regulations

### SEC / FINRA (US)

| Requirement | RISKCORE Support |
|-------------|------------------|
| Books and records retention | 5-year position history |
| Audit trail | Comprehensive audit logging |
| Data integrity | Validation pipeline |
| Access controls | RBAC, RLS |

### MiFID II (EU)

| Requirement | RISKCORE Support |
|-------------|------------------|
| Trade reporting | Export functionality |
| Best execution records | Trade capture with prices |
| Transaction reporting | Data export to client's reporting system |

### AIFMD (EU Alternative Investment Funds)

| Requirement | RISKCORE Support |
|-------------|------------------|
| Risk management | VaR, CVaR, exposures |
| Portfolio disclosure | Position reporting |
| Leverage calculation | Gross/net exposure |

---

## Security Controls by Tier

### Free Tier (Community)

| Control | Included |
|---------|----------|
| RBAC (6 roles) | ✅ |
| Row Level Security | ✅ |
| Password authentication | ✅ |
| TLS encryption in transit | ✅ |
| Input validation | ✅ |
| Audit logging | ✅ Basic |
| Rate limiting | ✅ Standard |
| MFA | ❌ |
| SSO/SAML | ❌ |
| IP whitelisting | ❌ |

### Pro Tier ($500-2K/month)

| Control | Included |
|---------|----------|
| Everything in Free | ✅ |
| MFA (TOTP) | ✅ |
| Extended audit logs (1 year) | ✅ |
| API access | ✅ |
| Priority support | ✅ |
| Security questionnaire response | ✅ |
| Vulnerability scan report | ✅ |

### Enterprise Tier ($5K-25K/month)

| Control | Included |
|---------|----------|
| Everything in Pro | ✅ |
| SSO/SAML integration | ✅ |
| Hardware MFA support | ✅ |
| IP whitelisting | ✅ |
| Custom data retention | ✅ |
| SOC 2 report (when available) | ✅ |
| Annual penetration test report | ✅ |
| Dedicated support channel | ✅ |
| SLA with uptime guarantee | ✅ |
| Security architecture review | ✅ |

---

## Compliance Roadmap

### Phase 1: Foundation (Current - MVP)

**Build compliant from day 1:**
- [x] RBAC with 6 roles
- [x] Row Level Security on all tables
- [x] Input validation pipeline
- [x] Audit logging framework
- [x] TLS 1.3 requirement
- [x] Secure password handling
- [ ] MFA implementation
- [ ] Privacy policy
- [ ] Terms of service

### Phase 2: Documentation ($0-100K ARR)

**Formalize compliance posture:**
- [ ] Security whitepaper
- [ ] Compliance FAQ
- [ ] DPA template
- [ ] Incident response plan
- [ ] Business continuity plan
- [ ] Security questionnaire (pre-filled)

### Phase 3: Validation ($100K-500K ARR)

**Third-party validation:**
- [ ] Penetration test (annual)
- [ ] Vulnerability assessment
- [ ] Security architecture review
- [ ] SOC 2 readiness assessment

### Phase 4: Certification ($500K+ ARR)

**Formal certification:**
- [ ] SOC 2 Type I audit
- [ ] SOC 2 Type II audit
- [ ] ISO 27001 (if market demands)

---

## Security Features Marketing Copy

### For Website / Tier Comparison

**Free Tier:**
> Built with enterprise-grade security foundations including role-based access control, multi-tenant isolation, encrypted communications, and comprehensive input validation.

**Pro Tier:**
> Enhanced security with multi-factor authentication, extended audit logging, API access controls, and security documentation support. Ideal for firms requiring formal security review.

**Enterprise Tier:**
> Maximum security posture with SSO/SAML integration, hardware MFA, IP whitelisting, custom retention policies, annual penetration testing, and SOC 2 report (when available). Designed for institutional requirements.

### Security Page Highlights

```
RISKCORE Security Architecture
──────────────────────────────

✓ Self-Hosted: Your data never leaves your infrastructure
✓ Read-Only: We never write back to source systems
✓ Zero Data Access: RISKCORE team has no access to your positions
✓ Multi-Tenant Isolation: PostgreSQL Row Level Security
✓ Encryption: TLS 1.3 in transit, AES-256 at rest (client configures)
✓ Access Control: 6-tier RBAC with granular book-level permissions
✓ Audit Trail: Comprehensive logging of all sensitive actions
✓ Input Validation: 11-rule validation pipeline
✓ Secure Development: Code review, dependency scanning, no secrets in code

Built following SOC 2 Trust Services Criteria:
• Security controls
• Availability measures
• Processing integrity
• Confidentiality protection
• Privacy by design
```

---

## Appendix: Compliance Checklist

### Pre-Launch

- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Cookie policy (if applicable)
- [ ] Security contact (security@riskcore.io)
- [ ] Responsible disclosure policy
- [ ] RBAC fully implemented
- [ ] RLS on all tables
- [ ] Audit logging active
- [ ] Input validation complete
- [ ] Password policy enforced
- [ ] TLS enforced

### Post-Launch (Phase 2)

- [ ] Security whitepaper
- [ ] DPA template available
- [ ] Incident response plan documented
- [ ] Business continuity plan documented
- [ ] Security questionnaire responses prepared
- [ ] MFA available for Pro tier

### Growth (Phase 3)

- [ ] First penetration test
- [ ] Vulnerability scanning automated
- [ ] SOC 2 readiness assessment
- [ ] SSO implementation for Enterprise

### Scale (Phase 4)

- [ ] SOC 2 Type I certification
- [ ] SOC 2 Type II certification
- [ ] Annual security program

---

*Document Version: 1.0*
*Created: 2026-01-13*
*Last Updated: 2026-01-13*

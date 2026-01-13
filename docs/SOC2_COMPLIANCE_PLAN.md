# RISKCORE SOC 2 Compliance Plan

> Comprehensive plan to achieve SOC 2 Type II certification for Pro and Enterprise tiers

---

## Executive Summary

This document outlines the roadmap for RISKCORE to achieve SOC 2 Type II certification for our paid tiers (Pro and Enterprise). SOC 2 compliance demonstrates our commitment to security and builds trust with hedge fund clients who require stringent data protection.

**Timeline:** 12-14 months to Type II certification
**Estimated Budget:** $55,000 - $90,000 (Year 1)
**Target Tiers:** Pro ($500-2K/month) and Enterprise ($5K-25K/month)

---

## What is SOC 2?

SOC 2 (System and Organization Controls 2) is an auditing framework developed by the AICPA that evaluates how organizations manage customer data based on five Trust Services Criteria:

| Criteria | Description | Required for RISKCORE? |
|----------|-------------|------------------------|
| **Security** | Protection against unauthorized access | **YES** (Required) |
| **Availability** | System availability for operation | **YES** (Enterprise SLA) |
| **Processing Integrity** | System processing is complete, accurate, timely | **YES** (Risk calculations) |
| **Confidentiality** | Information designated confidential is protected | **YES** (Position/trade data) |
| **Privacy** | Personal information collection, use, retention | Optional (B2B focus) |

### SOC 2 Types

| Type | Description | Duration | RISKCORE Target |
|------|-------------|----------|-----------------|
| **Type I** | Point-in-time assessment of control design | 1 audit | Month 8 |
| **Type II** | Operating effectiveness over 6+ months | Ongoing | Month 14 |

---

## Current State Assessment

### What We Already Have (from SECURITY.md)

| Control Area | Current State | SOC 2 Gap |
|--------------|---------------|-----------|
| **Access Control** | RBAC designed (6 roles) | Need formal access reviews |
| **Authentication** | Password-based planned | Need MFA for paid tiers |
| **Encryption at Rest** | PostgreSQL TDE planned | Need implementation + key management |
| **Encryption in Transit** | TLS 1.3 planned | Need certificate management |
| **Audit Logging** | Database triggers, user_email preserved | Need centralized SIEM |
| **Data Isolation** | Multi-tenant RLS | Compliant - strong design |
| **Network Security** | On-premises architecture | Need firewall documentation |
| **Incident Response** | Not documented | Need formal IR plan |
| **Vendor Management** | Not documented | Need vendor risk assessment |
| **Change Management** | Git-based | Need formal CAB process |
| **Business Continuity** | Not documented | Need BCP/DR plan |

### Risk Rating

| Area | Risk Level | Priority |
|------|------------|----------|
| Missing MFA | HIGH | P0 |
| No documented IR plan | HIGH | P0 |
| No change management process | MEDIUM | P1 |
| No vendor risk assessment | MEDIUM | P1 |
| No BCP/DR plan | MEDIUM | P1 |
| No penetration testing | MEDIUM | P2 |
| No security awareness training | LOW | P3 |

---

## Trust Services Criteria Implementation

### 1. Security (CC - Common Criteria)

The Security criteria forms the foundation of SOC 2 and is REQUIRED for all SOC 2 reports.

#### CC1: Control Environment

| Control | Implementation | Status |
|---------|----------------|--------|
| CC1.1 - Integrity & ethical values | Code of conduct document | TODO |
| CC1.2 - Board oversight | Advisory board for security | TODO |
| CC1.3 - Management structure | Organization chart with security roles | TODO |
| CC1.4 - Commitment to competence | Security training program | TODO |
| CC1.5 - Accountability | Security responsibilities in job descriptions | TODO |

#### CC2: Communication and Information

| Control | Implementation | Status |
|---------|----------------|--------|
| CC2.1 - Internal communication | Security policies distributed to employees | TODO |
| CC2.2 - External communication | Security page on website, customer notifications | TODO |
| CC2.3 - Security policies | Formal information security policy | TODO |

#### CC3: Risk Assessment

| Control | Implementation | Status |
|---------|----------------|--------|
| CC3.1 - Risk objectives | Annual risk assessment process | TODO |
| CC3.2 - Risk identification | Threat modeling for RISKCORE platform | TODO |
| CC3.3 - Fraud risk | Fraud risk assessment | TODO |
| CC3.4 - Change impact | Change management risk assessment | TODO |

#### CC4: Monitoring Activities

| Control | Implementation | Status |
|---------|----------------|--------|
| CC4.1 - Ongoing monitoring | Security dashboard, alert system | TODO |
| CC4.2 - Control deficiencies | Issue tracking, remediation process | TODO |

#### CC5: Control Activities

| Control | Implementation | Status |
|---------|----------------|--------|
| CC5.1 - Control selection | Risk-based control selection | TODO |
| CC5.2 - Technology controls | See technical controls below | IN PROGRESS |
| CC5.3 - Policy deployment | Control policies documented and deployed | TODO |

#### CC6: Logical and Physical Access Controls

| Control | Implementation | Status |
|---------|----------------|--------|
| CC6.1 - Logical access security | RBAC with 6 roles | DONE |
| CC6.2 - Access provisioning | User provisioning workflow | TODO |
| CC6.3 - Access removal | Offboarding checklist, automated deprovisioning | TODO |
| CC6.4 - Access restriction | Least privilege principle | DONE |
| CC6.5 - Authentication | MFA for Pro/Enterprise tiers | TODO |
| CC6.6 - Access review | Quarterly access reviews | TODO |
| CC6.7 - Physical access | On-premises client responsibility | N/A |
| CC6.8 - Physical access removal | On-premises client responsibility | N/A |

#### CC7: System Operations

| Control | Implementation | Status |
|---------|----------------|--------|
| CC7.1 - Vulnerability management | Regular vulnerability scanning | TODO |
| CC7.2 - Security monitoring | SIEM integration, alert rules | TODO |
| CC7.3 - Incident detection | IDS/IPS, anomaly detection | TODO |
| CC7.4 - Incident response | Documented IR plan | TODO |
| CC7.5 - Incident recovery | Recovery procedures | TODO |

#### CC8: Change Management

| Control | Implementation | Status |
|---------|----------------|--------|
| CC8.1 - Change authorization | Change Advisory Board (CAB) process | TODO |

#### CC9: Risk Mitigation

| Control | Implementation | Status |
|---------|----------------|--------|
| CC9.1 - Risk mitigation activities | Risk treatment plans | TODO |
| CC9.2 - Vendor risk management | Vendor assessment questionnaire | TODO |

---

### 2. Availability (A)

Required for Enterprise tier with SLA commitments.

| Control | Implementation | Status |
|---------|----------------|--------|
| A1.1 - Availability commitment | SLA documentation (99.9% uptime) | TODO |
| A1.2 - System recovery | Backup and recovery procedures | TODO |
| A1.3 - Recovery testing | Annual DR testing | TODO |

**Technical Implementation:**
- [ ] Automated database backups (daily)
- [ ] Point-in-time recovery capability
- [ ] Failover procedures documented
- [ ] RTO: 4 hours, RPO: 1 hour for Enterprise
- [ ] Uptime monitoring and alerting
- [ ] Status page for customers

---

### 3. Processing Integrity (PI)

Critical for risk calculations - hedge funds need to trust our numbers.

| Control | Implementation | Status |
|---------|----------------|--------|
| PI1.1 - Processing objectives | Data quality policies | PARTIAL |
| PI1.2 - Input validation | Validation pipeline (11 rules) | DONE |
| PI1.3 - Processing accuracy | Reconciliation procedures | TODO |
| PI1.4 - Output review | Output validation, audit trails | PARTIAL |
| PI1.5 - Error handling | Error handling and retry logic | DONE |

**Technical Implementation:**
- [x] Data validation pipeline with 11 rule types
- [x] Input sanitization and type checking
- [ ] Reconciliation reports for position data
- [x] Audit logging of all calculations
- [ ] Calculation verification procedures
- [ ] Data lineage documentation

---

### 4. Confidentiality (C)

Essential for position and trade data protection.

| Control | Implementation | Status |
|---------|----------------|--------|
| C1.1 - Confidentiality classification | Data classification policy | TODO |
| C1.2 - Confidentiality protection | Encryption, access controls | PARTIAL |

**Technical Implementation:**
- [x] Multi-tenant isolation with RLS
- [x] tenant_id on all data tables
- [ ] Data classification labels (Public, Internal, Confidential, Restricted)
- [ ] Encryption at rest (PostgreSQL TDE)
- [x] Encryption in transit (TLS 1.3)
- [ ] Key management procedures
- [ ] Data retention and disposal procedures
- [ ] Confidentiality agreements with vendors

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-3)

**Month 1: Governance & Documentation**
- [ ] Draft Information Security Policy
- [ ] Create Risk Assessment Framework
- [ ] Define data classification scheme
- [ ] Create incident response plan template
- [ ] Document current architecture and data flows

**Month 2: Access Management**
- [ ] Implement MFA for Pro/Enterprise tiers
- [ ] Create user provisioning procedures
- [ ] Create offboarding checklist
- [ ] Document access review process
- [ ] Implement password policy (complexity, rotation)

**Month 3: Technical Controls**
- [ ] Enable PostgreSQL TDE encryption
- [ ] Implement centralized logging (SIEM)
- [ ] Configure security alerting
- [ ] Document network architecture
- [ ] Implement vulnerability scanning

### Phase 2: Operations (Months 4-6)

**Month 4: Change Management**
- [ ] Create Change Management Policy
- [ ] Establish Change Advisory Board (CAB)
- [ ] Document emergency change procedures
- [ ] Create change request templates
- [ ] Implement change tracking system

**Month 5: Vendor Management**
- [ ] Create vendor risk assessment questionnaire
- [ ] Assess current vendors (OpenBB, FinancePy, etc.)
- [ ] Document vendor contracts and SLAs
- [ ] Create vendor review schedule

**Month 6: Business Continuity**
- [ ] Create Business Continuity Plan (BCP)
- [ ] Create Disaster Recovery Plan (DRP)
- [ ] Document backup procedures
- [ ] Define RTO/RPO objectives
- [ ] Schedule first DR test

### Phase 3: Type I Preparation (Months 7-8)

**Month 7: Gap Remediation**
- [ ] Complete all P0 and P1 items
- [ ] Conduct internal audit
- [ ] Remediate findings
- [ ] Collect evidence for controls
- [ ] Train team on audit process

**Month 8: Type I Audit**
- [ ] Select SOC 2 auditor
- [ ] Provide evidence to auditor
- [ ] Address auditor questions
- [ ] Receive Type I report
- [ ] Remediate any findings

### Phase 4: Type II Audit Period (Months 9-14)

**Months 9-13: Operating Period**
- [ ] Operate controls consistently
- [ ] Collect evidence monthly
- [ ] Conduct quarterly access reviews
- [ ] Perform monthly vulnerability scans
- [ ] Document all incidents
- [ ] Conduct tabletop DR exercise

**Month 14: Type II Audit**
- [ ] Provide 6 months of evidence
- [ ] Demonstrate control effectiveness
- [ ] Address auditor sampling requests
- [ ] Receive Type II report
- [ ] Publish SOC 2 badge on website

---

## Budget Estimate

### Year 1 Costs

| Category | Item | Low Estimate | High Estimate |
|----------|------|--------------|---------------|
| **Audit** | Type I Audit | $15,000 | $25,000 |
| **Audit** | Type II Audit | $20,000 | $35,000 |
| **Tools** | SIEM/Logging (Datadog, Splunk Cloud) | $5,000 | $10,000 |
| **Tools** | Vulnerability Scanner (Qualys, Nessus) | $3,000 | $5,000 |
| **Tools** | MFA Solution (Auth0, Okta) | $2,000 | $5,000 |
| **Consulting** | GRC Platform (Vanta, Drata) | $8,000 | $15,000 |
| **Training** | Security Awareness Training | $1,000 | $2,000 |
| **Testing** | Penetration Testing | $5,000 | $10,000 |
| | **TOTAL** | **$59,000** | **$107,000** |

### Ongoing Annual Costs (Year 2+)

| Category | Item | Annual Cost |
|----------|------|-------------|
| Audit | SOC 2 Type II Annual | $20,000 - $30,000 |
| Tools | SIEM/Logging | $5,000 - $10,000 |
| Tools | Vulnerability Scanner | $3,000 - $5,000 |
| Tools | MFA Solution | $2,000 - $5,000 |
| Tools | GRC Platform | $8,000 - $15,000 |
| Testing | Annual Penetration Test | $5,000 - $10,000 |
| | **TOTAL** | **$43,000 - $75,000** |

---

## GRC Platform Options

Consider using a GRC (Governance, Risk, Compliance) platform to streamline SOC 2 compliance:

| Platform | Starting Price | Features |
|----------|---------------|----------|
| **Vanta** | $10K/year | Auto-evidence collection, 100+ integrations |
| **Drata** | $10K/year | Continuous monitoring, employee onboarding |
| **Secureframe** | $8K/year | Automated compliance, audit management |
| **Sprinto** | $6K/year | Affordable, good for startups |
| **Laika** | $12K/year | Enterprise features, custom frameworks |

**Recommendation:** Vanta or Drata for best automation of evidence collection.

---

## Auditor Selection Criteria

When selecting a SOC 2 auditor:

| Criteria | Importance | Notes |
|----------|------------|-------|
| CPA firm licensed | Required | Must be AICPA member |
| SOC 2 experience | High | 50+ SOC 2 audits preferred |
| Fintech experience | High | Understands financial services |
| Reasonable pricing | Medium | $15K-35K for Type II |
| Responsive communication | Medium | Quick turnaround on questions |
| Clear deliverables | Medium | Know what you're getting |

**Recommended Auditors (Mid-Market):**
- Johanson Group
- Schellman
- A-LIGN
- Coalfire
- AssurancePoint

---

## Technical Implementation Checklist

### Authentication & Access

- [ ] Implement MFA using TOTP (Auth0, Okta, or custom)
- [ ] Password complexity: min 12 chars, upper/lower/number/special
- [ ] Password rotation: 90 days for Enterprise
- [ ] Account lockout after 5 failed attempts
- [ ] Session timeout: 30 minutes inactive
- [ ] JWT token expiration: 24 hours
- [ ] Refresh token rotation

### Encryption

- [ ] PostgreSQL TDE (Transparent Data Encryption)
- [ ] TLS 1.3 for all connections
- [ ] Certificate management (Let's Encrypt or enterprise CA)
- [ ] Key rotation schedule (annual)
- [ ] Backup encryption with separate keys
- [ ] API key hashing (bcrypt/argon2)

### Logging & Monitoring

- [ ] Centralized log aggregation (SIEM)
- [ ] Log retention: 1 year minimum
- [ ] Security event alerting
- [ ] Failed login attempt alerts
- [ ] Privilege escalation alerts
- [ ] Data export alerts
- [ ] API rate limit alerts

### Network Security

- [ ] Firewall rules documented
- [ ] Network segmentation (app, db, management)
- [ ] Intrusion detection system (IDS)
- [ ] DDoS protection (for hosted tiers)
- [ ] VPN for administrative access

### Vulnerability Management

- [ ] Weekly automated vulnerability scans
- [ ] Dependency scanning (Dependabot, Snyk)
- [ ] Annual penetration testing
- [ ] Vulnerability remediation SLAs:
  - Critical: 24 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

---

## Policy Documents Required

| Policy | Description | Priority |
|--------|-------------|----------|
| Information Security Policy | Master security policy | P0 |
| Acceptable Use Policy | Employee system usage rules | P1 |
| Access Control Policy | User provisioning, RBAC | P0 |
| Change Management Policy | CAB process, approvals | P1 |
| Incident Response Plan | Detection, response, recovery | P0 |
| Business Continuity Plan | Operations during disruption | P1 |
| Disaster Recovery Plan | System recovery procedures | P1 |
| Vendor Management Policy | Third-party risk assessment | P1 |
| Data Classification Policy | Data handling by sensitivity | P1 |
| Data Retention Policy | Retention and disposal | P2 |
| Encryption Policy | Encryption standards | P2 |
| Password Policy | Password requirements | P1 |
| Remote Work Policy | Secure remote access | P2 |
| Security Awareness Training | Training requirements | P2 |

---

## Tier-Specific Requirements

### Pro Tier ($500-2K/month)

| Feature | Requirement |
|---------|-------------|
| MFA | Required (TOTP) |
| SSO | Optional |
| Encryption | Standard (TDE + TLS) |
| Audit Logs | 90-day retention |
| Support | Business hours |
| SLA | 99.5% uptime |

### Enterprise Tier ($5K-25K/month)

| Feature | Requirement |
|---------|-------------|
| MFA | Required (TOTP + Hardware key option) |
| SSO | SAML 2.0 / OIDC |
| Encryption | Enhanced (customer-managed keys option) |
| Audit Logs | 1-year retention |
| Support | 24/7 with SLA |
| SLA | 99.9% uptime |
| Compliance | SOC 2 Type II report available |
| Penetration Testing | Annual, report shared |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| SOC 2 Type I | Pass | Month 8 |
| SOC 2 Type II | Pass | Month 14 |
| Zero critical findings | 0 | Audit report |
| Control effectiveness | >95% | Audit sampling |
| MFA adoption | 100% paid users | Monthly report |
| Incident response time | <1 hour detection | SIEM metrics |
| Vulnerability remediation | 100% within SLA | Scan reports |
| Employee training completion | 100% | LMS tracking |

---

## Next Steps

1. **Immediate (This Week)**
   - [ ] Review this plan with stakeholders
   - [ ] Decide on GRC platform (Vanta recommended)
   - [ ] Begin drafting Information Security Policy

2. **This Month**
   - [ ] Select and implement MFA solution
   - [ ] Set up centralized logging
   - [ ] Create incident response plan

3. **This Quarter**
   - [ ] Complete Phase 1 (Foundation)
   - [ ] Begin auditor selection process
   - [ ] Conduct first internal risk assessment

---

## References

- [AICPA SOC 2 Guide](https://www.aicpa.org/soc2)
- [SOC 2 Trust Services Criteria](https://us.aicpa.org/content/dam/aicpa/interestareas/frc/assuranceadvisoryservices/downloadabledocuments/trust-services-criteria.pdf)
- [RISKCORE Security Architecture](/docs/SECURITY.md)
- [RISKCORE Business Model](/docs/BUSINESS_MODEL.md)

---

*Document Version: 1.0*
*Created: 2026-01-13*
*Author: RISKCORE Team*

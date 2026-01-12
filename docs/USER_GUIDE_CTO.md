# RISKCORE Technical Guide for CTOs

> Architecture, integration, and deployment documentation
> **Audience:** Chief Technology Officers, IT Directors, System Architects
> **Last Updated:** 2026-01-12

---

## Executive Summary

RISKCORE is an **on-premises risk aggregation platform** designed for multi-manager hedge funds. Unlike cloud-based alternatives, RISKCORE ensures that all position, trade, and risk data remains on your infrastructure.

**Key Technical Principles:**
- 100% on-premises deployment (no cloud data storage)
- Direct PostgreSQL access (no intermediary cloud services)
- Multiple integration methods (REST API, FIX, CSV, Google Sheets)
- Multi-tenant architecture with row-level security
- Read-only overlay (never writes back to source systems)

---

## Architecture Overview

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        CLIENT INFRASTRUCTURE                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│  │  Bloomberg   │     │   Enfusion   │     │    Eze       │       │
│  │   AIM/EMSX   │     │              │     │   Eclipse    │       │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘       │
│         │                    │                    │                │
│         └──────────┬─────────┴────────┬──────────┘                │
│                    │                  │                            │
│              ┌─────▼─────┐      ┌─────▼─────┐                      │
│              │  FIX/API  │      │CSV/Excel/ │                      │
│              │  Adapter  │      │  Sheets   │                      │
│              └─────┬─────┘      └─────┬─────┘                      │
│                    │                  │                            │
│                    └────────┬─────────┘                            │
│                             │                                      │
│                    ┌────────▼────────┐                             │
│                    │    RISKCORE     │                             │
│                    │  FastAPI Server │                             │
│                    └────────┬────────┘                             │
│                             │                                      │
│                    ┌────────▼────────┐                             │
│                    │   PostgreSQL    │                             │
│                    │   (On-Premises) │                             │
│                    └─────────────────┘                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion:** Position/trade data flows from source systems via FIX, REST API, or file upload
2. **Processing:** RISKCORE normalizes, validates, and enriches data (security master resolution)
3. **Aggregation:** Cross-PM netting, overlap detection, correlation analysis
4. **Risk Calculation:** VaR, CVaR, Greeks, exposures computed
5. **Presentation:** Dashboard and API access for CRO, PMs, analysts

---

## Deployment Options

### Option 1: On-Premises Server (Recommended)

**Requirements:**
- Linux server (Ubuntu 22.04 LTS or RHEL 8+)
- 4+ CPU cores, 16GB+ RAM
- PostgreSQL 14+ (dedicated or shared)
- Python 3.11+

**Network:**
- Internal network access only (no public internet required)
- Firewall: Allow inbound on port 8000 (API) from internal IPs
- Optional: Reverse proxy (nginx) for TLS termination

### Option 2: Docker Deployment

```bash
# docker-compose.yml provided
docker-compose up -d

# Includes:
# - RISKCORE API container
# - PostgreSQL container
# - Volume mounts for data persistence
```

### Option 3: Kubernetes

Helm charts available for enterprise deployments with:
- Horizontal pod autoscaling
- PostgreSQL StatefulSet
- ConfigMaps for environment configuration
- Secrets management for credentials

---

## Integration Methods

### 1. REST API (Primary)

**Base URL:** `https://your-domain.internal/api/v1`

**Authentication:** API key in header
```
Authorization: Bearer <api_key>
```

**Key Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/positions` | Create single position |
| POST | `/positions/bulk` | Bulk position import |
| POST | `/trades` | Create single trade |
| POST | `/trades/bulk` | Bulk trade import |
| GET | `/aggregation/firm/summary` | Firm-wide risk summary |
| GET | `/correlation/pm/matrix` | PM correlation matrix |

**Example: Bulk Position Import**
```python
import requests

positions = [
    {
        "tenant_id": "uuid",
        "book_id": "uuid",
        "ticker": "AAPL",
        "quantity": 1000,
        "price": 150.00,
        "direction": "long"
    },
    # ... more positions
]

response = requests.post(
    "https://riskcore.internal/api/v1/positions/bulk",
    json={"positions": positions},
    headers={"Authorization": f"Bearer {api_key}"}
)
```

**Full API documentation:** `/docs` endpoint (Swagger/OpenAPI)

---

### 2. FIX Protocol

**Supported Message Types:**
- ExecutionReport (35=8) - Trade data
- PositionReport (35=AP) - Position snapshots

**FIX Version:** 4.2, 4.4

**Endpoint:** `POST /api/v1/fix/parse`

**Example:**
```python
fix_message = "8=FIX.4.2|35=8|49=SENDER|56=TARGET|55=AAPL|54=1|38=100|44=150.00|..."

response = requests.post(
    "https://riskcore.internal/api/v1/fix/parse",
    json={
        "message": fix_message,
        "tenant_id": "uuid",
        "book_id": "uuid",
        "import_data": True
    }
)
```

**Batch FIX Import:** `POST /api/v1/fix/parse/batch`

---

### 3. File Upload (CSV/Excel)

**Supported Formats:**
- CSV (.csv) - Any delimiter (auto-detected)
- Excel (.xlsx, .xls)

**Column Auto-Detection:**
System recognizes common column names:
- `ticker`, `symbol`, `security` → Security identifier
- `qty`, `quantity`, `shares` → Position size
- `price`, `px`, `last_price` → Current price
- `side`, `direction`, `long_short` → Position direction

**Endpoints:**
- `POST /api/v1/upload/preview` - Parse and preview
- `POST /api/v1/upload/import` - Import with mapping

**SFTP Integration:**
For automated daily imports, configure SFTP server to deposit files, then trigger import via API or scheduled job.

---

### 4. Google Sheets (Free Tier)

**Use Case:** Solo traders, small portfolios

**Requirements:**
- Sheet must be publicly shared ("Anyone with link can view")
- No authentication required from RISKCORE

**Endpoints:**
- `POST /api/v1/upload/google-sheets/preview`
- `POST /api/v1/upload/google-sheets/import`
- `GET /api/v1/upload/google-sheets/validate`

**Limitation:** Not suitable for sensitive institutional data

---

### 5. Watched Folder / Auto-Import (Enterprise)

**Use Case:** Automated daily imports from any OMS/EMS

**How It Works:**
1. Configure your OMS to export positions to a folder (or SFTP)
2. RISKCORE monitors the folder for new files
3. New files are automatically imported
4. Processed files move to an archive folder
5. Errors trigger notifications

**Supported Systems (via file export):**

| System | Export Method | Setup |
|--------|---------------|-------|
| Bloomberg AIM/PORT | CSV, FTP drop | Schedule report → drop folder |
| Enfusion | Report scheduler | SFTP to watched folder |
| Eze Eclipse | Report scheduler | CSV to network share |
| Charles River | Excel export | Manual or scheduled |
| Prime Brokers | Daily files | SFTP or shared folder |

**Key Benefit:** No vendor API partnerships required. Works with ANY system that can export a file.

**Configuration:**
```yaml
# config/watched_folders.yaml
folders:
  - path: /data/imports/bloomberg
    type: positions
    tenant_id: <uuid>
    book_id: <uuid>
    poll_interval: 60  # seconds
    archive_path: /data/imports/archive

  - path: /data/imports/enfusion
    type: trades
    tenant_id: <uuid>
    poll_interval: 300
```

**SFTP Integration:**
For secure file transfers, RISKCORE can connect to SFTP servers:
```yaml
sftp:
  host: sftp.yourfirm.internal
  port: 22
  username: riskcore
  key_file: /path/to/key
  remote_path: /exports/positions
  local_path: /data/imports/sftp
```

---

## Database Schema

### Core Tables

| Table | Purpose | Row-Level Security |
|-------|---------|-------------------|
| `tenants` | Multi-tenant isolation | N/A |
| `users` | User accounts | By tenant |
| `books` | PM portfolios | By tenant |
| `positions` | Current positions | By tenant |
| `trades` | Trade history | By tenant |
| `securities` | Global security master | Public |
| `risk_metrics` | Calculated metrics | By tenant |

### Security Model

- **Row-Level Security (RLS):** All queries filtered by `tenant_id`
- **Column Encryption:** Sensitive fields encrypted at rest
- **Audit Logging:** All data access logged with user, timestamp, action

---

## Security & Compliance

### Data Residency

- **Default:** All data on your infrastructure
- **Cloud Option:** None (by design)
- **Backups:** Your responsibility (standard PostgreSQL backup tools)

### Authentication & Authorization

| Feature | Implementation |
|---------|---------------|
| User Authentication | Email/password + optional 2FA |
| API Authentication | API keys with scopes |
| SSO/SAML | Enterprise tier (Phase 2) |
| Role-Based Access | 6 roles (SuperAdmin → Analyst) |

### Encryption

- **In Transit:** TLS 1.3 required
- **At Rest:** PostgreSQL encryption (your config)
- **API Keys:** Hashed with bcrypt

### Audit Trail

All sensitive operations logged:
- Position/trade creates, updates, deletes
- User logins and permission changes
- Export operations
- Admin configuration changes

---

## System Requirements

### Minimum (Development/Testing)

| Component | Specification |
|-----------|---------------|
| CPU | 2 cores |
| RAM | 8 GB |
| Storage | 50 GB SSD |
| PostgreSQL | 14+ |
| Python | 3.11+ |

### Recommended (Production)

| Component | Specification |
|-----------|---------------|
| CPU | 8+ cores |
| RAM | 32 GB |
| Storage | 500 GB SSD (NVMe preferred) |
| PostgreSQL | 15+ with connection pooling |
| Python | 3.11+ |
| Network | 1 Gbps internal |

### Scaling Considerations

- **Horizontal:** Multiple API servers behind load balancer
- **Database:** Read replicas for reporting queries
- **Caching:** Redis for computed risk metrics (optional)

---

## Integration Checklist

### Pre-Integration

- [ ] PostgreSQL server provisioned
- [ ] Network connectivity verified (API server → DB)
- [ ] Firewall rules configured
- [ ] SSL certificates obtained (internal CA or Let's Encrypt)
- [ ] Service account credentials prepared

### Integration Steps

1. **Deploy RISKCORE**
   ```bash
   git clone https://github.com/massimotodaro/riskcore.git
   cd riskcore
   pip install -r backend/requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # .env file
   DATABASE_URL=postgresql://user:pass@localhost:5432/riskcore
   API_SECRET_KEY=your-secret-key
   ```

3. **Initialize Database**
   ```bash
   # Apply migrations
   psql -f supabase/migrations/*.sql
   ```

4. **Start Service**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

5. **Verify**
   ```bash
   curl http://localhost:8000/api/v1/health
   # {"status": "healthy"}
   ```

### Post-Integration

- [ ] Create tenant and admin user
- [ ] Configure API keys for integrations
- [ ] Test position import from source system
- [ ] Verify aggregation calculations
- [ ] Set up monitoring and alerting

---

## API Rate Limits

| Tier | Requests/Minute | Concurrent |
|------|-----------------|------------|
| Free | 100 | 5 |
| Pro | 1,000 | 50 |
| Enterprise | 10,000 | Unlimited |

---

## Monitoring & Observability

### Health Endpoints

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/db` - Database connectivity
- `GET /api/v1/health/detailed` - Full system status

### Metrics (Prometheus Compatible)

- Request latency (p50, p95, p99)
- Error rates by endpoint
- Database connection pool status
- Active users

### Logging

- JSON structured logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracing

---

## Support & Resources

### Documentation

- API Reference: `/docs` (Swagger UI)
- GitHub Wiki: https://github.com/massimotodaro/riskcore/wiki
- This guide: `/docs/USER_GUIDE_CTO.md`

### Support Channels

| Tier | Support |
|------|---------|
| Free | GitHub Issues |
| Pro | Email support (24h response) |
| Enterprise | Dedicated Slack channel, SLA |

### Contact

- **Technical:** tech@riskcore.io (future)
- **Sales:** sales@riskcore.io (future)
- **GitHub:** https://github.com/massimotodaro/riskcore

---

*Questions? Contact your RISKCORE implementation team or open a GitHub issue.*

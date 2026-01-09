# RISKCORE

> Open-source multi-manager risk aggregation platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Under Development](https://img.shields.io/badge/status-under%20development-orange.svg)]()

---

## The Problem

Multi-manager hedge funds have PMs using different systems:

- PM 1 uses **Bloomberg AIM**
- PM 2 uses **Charles River**
- PM 3 uses **Excel**
- PM 4 uses **Enfusion**

**No platform aggregates risk across all of them.**

Central risk teams cobble together spreadsheets. They can't answer simple questions like:
- "What's our firm-wide exposure to tech?"
- "Which PMs have offsetting positions?"
- "What's our total VaR?"

**RISKCORE solves this.**

---

## What RISKCORE Does

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXISTING SYSTEMS (Don't touch)                 │
├─────────────────────────────────────────────────────────────────┤
│  PM 1: Bloomberg    PM 2: Enfusion    PM 3: Excel    PM 4: Eze  │
│         │                │                │              │      │
│         └────────────────┼────────────────┼──────────────┘      │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      RISKCORE                            │   │
│  │      (sits on top, reads everything, writes nothing)     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Multi-PM Aggregation** — Consolidate positions across any number of PMs and systems
- **Cross-PM Netting** — Identify offsetting positions automatically
- **Firm-wide Risk** — Calculate VaR, exposures, concentration at the firm level
- **Source-Agnostic** — Connect via file upload, API, or database
- **AI-Powered Queries** — Ask questions in natural language
- **Beautiful Dashboard** — Real-time, responsive, modern UI

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/riskcore.git
cd riskcore

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

---

## How It Works

### 1. Ingest Positions

Upload files or connect APIs:

```python
# Upload CSV
curl -X POST http://localhost:8000/api/v1/positions/upload \
  -F "file=@positions.csv"

# Or use the API
curl -X POST http://localhost:8000/api/v1/positions \
  -H "Content-Type: application/json" \
  -d '{"portfolio": "PM_Alpha", "ticker": "AAPL", "quantity": 1000}'
```

### 2. Aggregate & Analyze

RISKCORE normalizes data, maps securities, and aggregates:

```python
# Get firm-wide exposures
GET /api/v1/risk/exposures

# Get cross-PM overlaps
GET /api/v1/risk/overlaps

# Get VaR
GET /api/v1/risk/var
```

### 3. Query with AI

Ask questions in natural language:

```
"What's our net exposure to tech across all PMs?"
"Show me positions where PM1 and PM3 have opposite views"
"Run a stress test: rates +100bps"
```

---

## Architecture

| Layer | Description |
|-------|-------------|
| **Data Ingestion** | File upload, REST API, database connectors |
| **Pricing** | FinancePy for derivatives, OpenBB for market data |
| **Aggregation** | Multi-PM consolidation, security master, netting |
| **Risk Engine** | VaR, exposures, stress testing (via Riskfolio-Lib) |
| **AI Layer** | Natural language queries (Claude API) |
| **Dashboard** | React + Tailwind, real-time updates |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Database | Supabase (PostgreSQL) |
| Backend | Python, FastAPI |
| Frontend | React, Tailwind, Recharts |
| Risk Metrics | Riskfolio-Lib |
| Pricing | FinancePy |
| Market Data | OpenBB |
| AI | Claude API |

---

## Supported Integrations

### Now (MVP)

| System | Method |
|--------|--------|
| CSV/Excel | File upload |
| JSON | API |

### Coming Soon

| System | Method |
|--------|--------|
| Enfusion | REST API |
| Eze Eclipse | REST API |
| Bloomberg | BLPAPI |
| Database | Read replica |
| FIX | Protocol listener |

---

## Documentation

- [Architecture](/docs/ARCHITECTURE.md)
- [MVP Scope](/docs/MVP.md)
- [Tech Stack](/docs/TECH_STACK.md)
- [Integration Guide](/docs/INTEGRATION.md)
- [Pricing Layer](/docs/PRICING.md)

---

## Why Open Source?

1. **Trust** — See exactly what the code does
2. **Flexibility** — Customize for your needs
3. **Community** — Contribute and improve together
4. **No Lock-in** — Run it yourself, forever

---

## Roadmap

- [x] Market research & competitor analysis
- [x] Architecture design
- [ ] Database schema
- [ ] Position ingestion API
- [ ] Risk calculations
- [ ] Aggregation engine
- [ ] Dashboard
- [ ] AI integration
- [ ] Enfusion connector
- [ ] Eze connector

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## About

Built by [Massimo Todaro](https://linkedin.com/in/massimotodaro) — 20+ years in finance (Barclays Capital, hedge funds, fintech).

Questions? Open an issue or reach out on LinkedIn.

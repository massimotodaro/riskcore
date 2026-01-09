# RISKCORE Tech Stack

> Last Updated: 2025-01-09

## Build vs Buy Strategy

**Leverage proven open-source libraries. Build only what makes RISKCORE unique.**

| Layer | Approach | Solution | Notes |
|-------|----------|----------|-------|
| Market Data | Use existing | **OpenBB** | 100+ data providers |
| Pricing Models | Use existing | **FinancePy** | Derivatives, curves, Greeks |
| Risk Measures | Use existing | **Riskfolio-Lib** | 24 risk measures, VaR, CVaR |
| Database | Use existing | **Supabase** | Postgres + real-time |
| Position Aggregation | **BUILD** | RISKCORE core | Our unique value |
| IBOR | **BUILD** | RISKCORE core | No open-source exists |
| Cross-PM Netting | **BUILD** | RISKCORE core | Our unique value |
| Firm-wide VaR | **BUILD** | RISKCORE core | Aggregated risk |
| AI Queries | **BUILD** | Claude API | Natural language |
| Dashboard | **BUILD** | React + Tailwind | User interface |

---

## Implementation Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Database | **Supabase** | Already set up, real-time subscriptions, free tier, project `vukinjdeddwwlaumtfij` |
| Backend | **Python + FastAPI** | Industry standard, integrates with FinancePy/Riskfolio |
| Frontend | **React + Tailwind** | Beautiful, professional, component-based |
| Charts | **Recharts / Tremor** | Modern, React-native, clean |
| AI | **Claude API** | Natural language risk queries |
| Market Data | **OpenBB + Yahoo** | Free for MVP, upgrade path to Bloomberg |
| Hosting | **Vercel + Railway** | Free tier, easy deployment |
| Repo | **GitHub (public)** | Open-source visibility, thought leadership |

---

## Key Open-Source Libraries

### OpenBB (Market Data)

- **URL:** https://github.com/OpenBB-finance/OpenBB
- **Stars:** 31,000+
- **License:** AGPL-3.0
- **Use for:** Market data from 100+ providers
- **Install:** `pip install openbb`

### FinancePy (Pricing)

- **URL:** https://github.com/domokane/FinancePy
- **Stars:** 2,600+
- **License:** MIT
- **Use for:** Derivatives pricing, yield curves, Greeks
- **Install:** `pip install financepy`

Capabilities:
- Fixed income (bonds, swaps, swaptions)
- Equity derivatives (options, variance swaps)
- FX derivatives
- Credit derivatives (CDS, CDO)
- Interest rate models
- Curve construction

### Riskfolio-Lib (Risk Metrics)

- **URL:** https://github.com/dcajasn/Riskfolio-Lib
- **Stars:** 3,000+
- **License:** BSD-3
- **Use for:** VaR, CVaR, covariance, 24 risk measures
- **Install:** `pip install riskfolio-lib`

Capabilities:
- 24 convex risk measures
- CVaR, EVaR, RLVaR
- Drawdown measures (CDaR, EDaR)
- Covariance estimation
- Risk parity

### QuantStats (Performance)

- **URL:** https://github.com/ranaroussi/quantstats
- **Stars:** 4,500+
- **License:** Apache 2.0
- **Use for:** Performance reporting, tear sheets
- **Install:** `pip install quantstats`

---

## Python Dependencies

```txt
# requirements.txt

# Web framework
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6

# Database
supabase>=2.0.0
asyncpg>=0.28.0

# Data processing
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0  # Excel files

# Finance libraries (DO NOT REBUILD)
openbb>=4.0.0
financepy>=0.350
riskfolio-lib>=6.0.0
quantstats>=0.0.62

# AI
anthropic>=0.18.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
httpx>=0.24.0
```

---

## Frontend Dependencies

```json
// package.json dependencies
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "tailwindcss": "^3.4.0",
    "@supabase/supabase-js": "^2.39.0",
    "recharts": "^2.10.0",
    "@tremor/react": "^3.14.0",
    "lucide-react": "^0.300.0"
  }
}
```

---

## Project Structure

```
/riskcore
├── CLAUDE.md                 # Project context for CC
├── README.md                 # Public README
├── LICENSE                   # MIT License
│
├── /docs                     # Documentation
│   ├── ARCHITECTURE.md
│   ├── MVP.md
│   ├── TECH_STACK.md
│   ├── COMPETITORS.md
│   ├── GITHUB_RESEARCH.md
│   ├── PRICING.md
│   ├── INTEGRATION.md
│   └── DECISIONS.md
│
├── /backend                  # Python FastAPI
│   ├── main.py
│   ├── requirements.txt
│   ├── /api
│   │   ├── positions.py
│   │   ├── portfolios.py
│   │   ├── risk.py
│   │   └── ai.py
│   ├── /core
│   │   ├── aggregation.py    # CORE: Our unique value
│   │   ├── security_master.py
│   │   ├── netting.py
│   │   └── pricing.py
│   ├── /integrations
│   │   ├── file_parser.py
│   │   ├── enfusion.py
│   │   └── eze.py
│   └── /tests
│
├── /frontend                 # React + Tailwind
│   ├── package.json
│   ├── /src
│   │   ├── /components
│   │   ├── /pages
│   │   └── /hooks
│   └── /public
│
├── /database                 # Schema and migrations
│   ├── schema.sql
│   └── seed.sql
│
├── /scripts                  # Utilities
│   ├── generate_mock_data.py
│   └── setup.sh
│
└── /examples                 # Sample data files
    ├── sample_positions.csv
    ├── sample_positions.xlsx
    └── sample_positions.json
```

---

## Environment Variables

```bash
# .env.example

# Supabase
SUPABASE_URL=https://vukinjdeddwwlaumtfij.supabase.co
SUPABASE_KEY=your_key_here

# Claude AI
ANTHROPIC_API_KEY=your_key_here

# OpenBB (optional, for premium data)
OPENBB_TOKEN=your_token_here

# Environment
ENVIRONMENT=development
DEBUG=true
```

---

## Development Setup

```bash
# Clone repo
git clone https://github.com/yourusername/riskcore.git
cd riskcore

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys

# Start backend
uvicorn main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

---

## Deployment

### Backend (Railway)

```bash
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

### Frontend (Vercel)

- Connect GitHub repo
- Framework preset: Next.js
- Environment variables: Add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

## API Design

### Endpoints (MVP)

```
POST   /api/v1/positions/upload     # Upload file (CSV, Excel)
POST   /api/v1/positions            # Create position
GET    /api/v1/positions            # List positions
GET    /api/v1/positions/{id}       # Get position

GET    /api/v1/portfolios           # List portfolios
GET    /api/v1/portfolios/{id}      # Get portfolio with positions

GET    /api/v1/risk/exposures       # Get exposure breakdown
GET    /api/v1/risk/var             # Get VaR metrics
GET    /api/v1/risk/overlaps        # Get cross-PM overlaps

POST   /api/v1/ai/query             # Natural language query
```

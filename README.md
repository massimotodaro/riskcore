# RISKCORE

**Open-source multi-strategy risk aggregation platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)

> 🚧 **Under Development** — Star this repo to follow progress

## The Problem

Multi-manager hedge funds and asset managers operate with a fundamental blind spot: **they cannot see aggregated risk across portfolio managers who use different systems.**

Each PM runs their own book with their preferred tools—Bloomberg PORT, Axioma, RiskMetrics, internal spreadsheets—creating data silos that make firm-wide risk aggregation nearly impossible. When the CRO asks "what's our total tech exposure?" or "are we net long or short the market?", the answer requires hours of manual data gathering and spreadsheet gymnastics.

This fragmentation leads to:
- **Delayed risk reporting** — Hours or days to produce firm-level views
- **Missed netting opportunities** — PMs unknowingly take offsetting positions
- **Regulatory headaches** — Manual aggregation for compliance reporting
- **Crisis blind spots** — No real-time view during market stress

## The Solution

RiskCore ingests position and risk data from any source, normalizes it into a unified schema, and provides real-time aggregated views across the entire firm.

## Key Features (Planned)

| Feature | Description |
|---------|-------------|
| **Real-time Position Aggregation** | Consolidate positions across all PMs and systems into a single view |
| **Cross-PM Netting** | Identify offsetting positions and calculate true net exposures |
| **Firm-level VaR** | Aggregate Value-at-Risk with proper correlation handling |
| **Exposure Analytics** | Slice exposures by sector, geography, asset class, factor, or custom tags |
| **AI-Powered Queries** | Ask questions in natural language: *"What's our net delta to semiconductors?"* |

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Database** | Supabase (PostgreSQL + Real-time subscriptions) |
| **Backend** | Python, FastAPI |
| **Frontend** | React, TypeScript, TailwindCSS |
| **AI** | Claude API (Anthropic) |

## Project Structure

```
riskcore/
├── backend/         # FastAPI application
├── frontend/        # React dashboard
├── database/        # Supabase schema and migrations
├── docs/            # Documentation
├── examples/        # Sample data and notebooks
├── LICENSE
└── README.md
```

## Getting Started

```bash
# Clone the repository
git clone https://github.com/yourusername/riskcore.git
cd riskcore

# Setup instructions coming soon
```

## Roadmap

- [ ] Database schema design
- [ ] Position ingestion API
- [ ] Basic aggregation engine
- [ ] Web dashboard MVP
- [ ] VaR calculation engine
- [ ] Natural language query interface
- [ ] Real-time streaming updates

## Contributing

Contributions are welcome! This project is in early development—check the issues for ways to help.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>Built for the buy-side</i>
</p>

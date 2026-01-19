# RISKCORE AI Architecture Research

> **Date:** 2026-01-19
> **Status:** RESEARCH COMPLETE - IMPLEMENTATION PENDING
> **Context:** Discussion about on-premises AI for competitive advantage

---

## Executive Summary

RISKCORE will be an **AI-first platform** with 100% on-premises inference capability. This is a massive differentiator - no other risk platform offers AI that runs locally without sending data to the cloud.

**Key Insight:** We don't need a giant model. For domain-specific applications like RISKCORE, a 3B parameter model with proper RAG will outperform GPT-4 because:
- It's focused on one task
- It has all context via retrieval
- It calls tools (SQL, calculations) rather than guessing

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISKCORE ON-PREMISES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Embedding   │    │   Vector     │    │   Small LLM      │  │
│  │    Model     │───▶│   Store      │───▶│   (3-7B params)  │  │
│  │  (300M-1B)   │    │  (pgvector)  │    │   Local Inference│  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                     │             │
│         ▼                   ▼                     ▼             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    RISKCORE DATA                         │   │
│  │   Positions │ Trades │ Risk Metrics │ Documentation     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Two-Model Architecture

### 1. Embedding Model (for Search & Retrieval)

**Purpose:** Convert text → vectors for semantic search

| Model | Size | Use Case |
|-------|------|----------|
| **Gemma Embedding (2B)** | ~300M-2B params | Google's new model, excellent quality |
| **nomic-embed-text** | 137M params | Very fast, good quality |
| **bge-small-en** | 33M params | Tiny, runs anywhere |
| **all-MiniLM-L6-v2** | 22M params | Industry standard, battle-tested |

These are **tiny** and run instantly on any CPU.

### 2. Generation Model (for Answering Questions)

**Purpose:** Take retrieved context + user question → natural language answer

| Model | Params | Memory (4-bit) | Speed | Quality |
|-------|--------|----------------|-------|---------|
| **Phi-3-mini** | 3.8B | ~2GB RAM | Fast on CPU | Excellent |
| **Qwen2.5-3B** | 3B | ~2GB RAM | Fast on CPU | Very good |
| **Llama-3.2-3B** | 3B | ~2GB RAM | Fast on CPU | Very good |
| **Mistral-7B** | 7B | ~4GB RAM | Needs GPU ideally | Excellent |
| **Llama-3.1-8B** | 8B | ~5GB RAM | Needs GPU | Best quality |

---

## Why Small Models Work for RISKCORE

For RISKCORE, the AI needs to:

1. **Understand structured queries**: "What's my net tech exposure?" → SQL query
2. **Summarize numbers**: "Explain my VaR breach" → formatted explanation
3. **Domain knowledge**: Financial terms, risk concepts (can be fine-tuned or RAG'd)
4. **NOT** general knowledge, creative writing, coding, etc.

A **3B parameter model** fine-tuned or prompted correctly will outperform GPT-4 for this specific domain because:
- It's focused on one task
- It has all context via RAG
- It's calling tools (SQL, calculations) rather than guessing

---

## What Gets Vectorized (Embedded)

```python
# Things we embed and store in pgvector:

1. Position descriptions
   "AAPL long 10,000 shares in Alpha Fund tech book"

2. Risk metric explanations
   "VaR 95% measures the maximum expected loss over 1 day
    with 95% confidence"

3. Platform documentation
   "To add a new RiskPod, click the + button..."

4. Historical context
   "On Jan 15, PM John Smith increased tech exposure by 20%"

5. Instrument metadata
   "AAPL: Apple Inc, Technology sector, S&P 500 constituent"
```

---

## Example Query Flow

```
User: "Why did my equity VaR increase yesterday?"

1. EMBED the question → vector

2. SEARCH pgvector for similar content:
   - Found: Position changes from yesterday
   - Found: VaR calculation methodology
   - Found: Equity book composition

3. CONSTRUCT prompt for small LLM:
   "Given this context: [retrieved docs]
    Answer: Why did equity VaR increase?"

4. LLM GENERATES focused answer:
   "Your equity VaR increased by $240K (+12%) yesterday due to:
    1. New NVDA position (+$2.1M notional)
    2. Increased correlation in tech sector (0.72 → 0.81)
    3. VIX moved from 14.2 to 16.8"
```

---

## Hardware Requirements

### Minimum (CPU only, 3B model)
- 8GB RAM
- Any modern CPU (Intel i5/AMD Ryzen 5+)
- Response time: 2-5 seconds

### Recommended (GPU, 7B model)
- 16GB RAM
- NVIDIA RTX 3060+ (8GB VRAM)
- Response time: <1 second

### Enterprise (multiple users)
- 32GB+ RAM
- NVIDIA RTX 4080/A10 (16GB VRAM)
- Response time: <0.5 seconds, concurrent users

---

## Technical Stack Options

### Inference Layer

```
Option A: Ollama (easiest)
- One command install
- Manages models automatically
- REST API compatible
- ollama run phi3

Option B: llama.cpp (fastest)
- Pure C++, no dependencies
- GGUF quantized models
- Best performance on CPU

Option C: vLLM (if GPU available)
- Production-grade
- Batching, streaming
- Best for multiple users
```

---

## Implementation Phases

### Phase 1 (MVP)

| Component | Choice | Notes |
|-----------|--------|-------|
| Embedding | all-MiniLM-L6-v2 (22M) or nomic-embed-text | Tiny, fast |
| Vector DB | pgvector | Already using PostgreSQL! |
| LLM | Phi-3-mini-4k (3.8B, 4-bit) | Best quality/size ratio |
| Inference | Ollama | Simplest deployment |
| Integration | Python + FastAPI endpoints | Standard stack |

### Phase 2 (Production)

| Component | Choice | Notes |
|-----------|--------|-------|
| Embedding | Gemma Embedding 2B | Better quality |
| LLM | Qwen2.5-7B or Llama-3.1-8B | If clients have GPU |
| Fine-tuning | Train on financial/risk Q&A pairs | Domain expertise |
| Inference | llama.cpp or vLLM | Performance |

---

## Competitive Advantage

| Competitor | AI Approach | Problem |
|------------|-------------|---------|
| Bloomberg | Cloud API | Data leaves premises |
| Enfusion | No AI | Manual analysis |
| RiskVal | No AI | Manual analysis |
| **RISKCORE** | **On-prem AI** | **None - data stays local** |

This is genuinely unique. No risk platform offers AI that:
1. Runs 100% locally
2. Never sends data to cloud
3. Understands your specific positions
4. Answers in natural language

---

## Google Gemma Embedding Context

Google released a 300M parameter embedding model specifically designed to be embedded in systems for vectorization. This aligns perfectly with our architecture:

- **Small enough** to run on any hardware
- **Designed for** document retrieval and semantic search
- **Open weights** for on-premises deployment
- **No cloud dependency**

---

## Action Items (When We Start Week 6)

1. **Prototype AI layer** - Add Ollama integration with Phi-3 to the backend
2. **Design chat interface** - How it appears in the Riskboard UI
3. **Research fine-tuning** - How to train a small model on risk/finance data
4. **Explore Gemma embedding** - Test it for our use case

---

## References

- ROADMAP.md Week 6 section for full implementation milestones
- STATE.md Session 17 for discussion context
- docs/SECURITY.md for data handling requirements

---

*Document created: 2026-01-19*
*To be implemented: Week 6 (AI Assistant)*

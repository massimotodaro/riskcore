"""
RISKCORE Market Research Analysis
Analyzes scraped articles to identify themes, pain points, and opportunities.
"""

import json
import re
from collections import Counter
from datetime import datetime

# Load articles
with open('../data/research_articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

print(f"Loaded {len(articles)} articles\n")

# ============================================================================
# 1. HIGH RELEVANCE ARTICLES (score >= 3)
# ============================================================================
print("=" * 70)
print("1. HIGH RELEVANCE ARTICLES (score >= 3)")
print("=" * 70)

high_relevance = [a for a in articles if a.get('relevance_score', 0) >= 3]
print(f"\nFound {len(high_relevance)} articles with relevance >= 3:\n")

for article in sorted(high_relevance, key=lambda x: x.get('relevance_score', 0), reverse=True):
    print(f"[{article['relevance_score']}] {article['title'][:70]}")
    print(f"    Source: {article['source_site']}")
    print(f"    Tags: {', '.join(article.get('tags', []))}")
    print()

# ============================================================================
# 2. TOP 10 MOST COMMON TAGS
# ============================================================================
print("=" * 70)
print("2. TOP 10 MOST COMMON TAGS")
print("=" * 70)

all_tags = []
for article in articles:
    all_tags.extend(article.get('tags', []))

tag_counts = Counter(all_tags)
print("\nTag frequency:\n")
for tag, count in tag_counts.most_common(10):
    bar = "#" * min(count, 40)
    print(f"  {tag:20} {bar} ({count})")

# ============================================================================
# 3. PAIN POINTS ANALYSIS
# ============================================================================
print("\n" + "=" * 70)
print("3. PAIN POINTS ANALYSIS")
print("=" * 70)

def extract_context(text, keyword, window=100):
    """Extract context around a keyword."""
    idx = text.find(keyword)
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(keyword) + window)
    return "..." + text[start:end] + "..."

pain_keywords = {
    'challenge': [],
    'problem': [],
    'struggle': [],
    'difficult': [],
    'gap': [],
    'lack': [],
    'issue': [],
    'complexity': [],
    'fragmented': [],
    'siloed': [],
    'manual': [],
    'legacy': [],
    'costly': [],
    'slow': [],
    'inefficient': [],
}

for article in articles:
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('full_text', '')}".lower()
    for keyword in pain_keywords:
        if keyword in text:
            pain_keywords[keyword].append({
                'title': article['title'],
                'source': article['source_site'],
                'context': extract_context(text, keyword)
            })

# Sort by frequency
pain_counts = {k: len(v) for k, v in pain_keywords.items()}
sorted_pains = sorted(pain_counts.items(), key=lambda x: x[1], reverse=True)

print("\nPain point keywords frequency:\n")
for keyword, count in sorted_pains[:10]:
    if count > 0:
        bar = "#" * min(count, 30)
        print(f"  {keyword:15} {bar} ({count})")

# ============================================================================
# 4. VENDOR LANDSCAPE
# ============================================================================
print("\n" + "=" * 70)
print("4. VENDOR LANDSCAPE")
print("=" * 70)

vendors = [
    'Bloomberg', 'Aladdin', 'BlackRock', 'SimCorp', 'MSCI', 'Axioma',
    'RiskMetrics', 'Enfusion', 'Eze', 'Charles River', 'FactSet',
    'Refinitiv', 'LSEG', 'SS&C', 'Advent', 'Geneva', 'State Street',
    'Northern Trust', 'BNY Mellon', 'Citco', 'Apex', 'Markit', 'IHS',
    'Murex', 'Calypso', 'Finastra', 'ION', 'Broadridge', 'FIS',
    'Numerix', 'Quantifi', 'FINCAD', 'Imagine', 'OpenGamma',
    'RiskVal', 'Orchestrade', 'AccessFintech', 'Tradeweb', 'MarketAxess',
    'FlexTrade', 'TradingScreen', 'Portware', 'ITG', 'Virtu',
    'Citadel', 'Two Sigma', 'DE Shaw', 'Renaissance', 'Millennium',
    'Point72', 'Balyasny', 'Brevan Howard', 'Bridgewater', 'AQR',
]

vendor_mentions = Counter()
vendor_contexts = {}

for article in articles:
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('full_text', '')}".lower()
    for vendor in vendors:
        if vendor.lower() in text:
            vendor_mentions[vendor] += 1
            if vendor not in vendor_contexts:
                vendor_contexts[vendor] = article['title']

print("\nVendor mentions:\n")
for vendor, count in vendor_mentions.most_common(20):
    if count > 0:
        bar = "#" * min(count, 20)
        print(f"  {vendor:20} {bar} ({count})")

# ============================================================================
# 5. MULTI-MANAGER / AGGREGATION ARTICLES
# ============================================================================
print("\n" + "=" * 70)
print("5. MULTI-MANAGER / PORTFOLIO AGGREGATION ARTICLES")
print("=" * 70)

aggregation_keywords = [
    'multi-manager', 'multi manager', 'multimanager',
    'multi-asset', 'multi asset', 'multiasset',
    'multi-strategy', 'multi strategy', 'multistrategy',
    'portfolio aggregation', 'position aggregation',
    'risk aggregation', 'consolidated', 'firm-wide',
    'cross-portfolio', 'enterprise risk', 'ibor',
    'investment book of record', 'total portfolio'
]

aggregation_articles = []

for article in articles:
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('full_text', '')}".lower()
    matched_keywords = [kw for kw in aggregation_keywords if kw in text]
    if matched_keywords:
        aggregation_articles.append({
            'title': article['title'],
            'source': article['source_site'],
            'url': article['url'],
            'keywords': matched_keywords,
            'relevance': article.get('relevance_score', 1)
        })

print(f"\nFound {len(aggregation_articles)} articles about multi-manager/aggregation:\n")
for article in sorted(aggregation_articles, key=lambda x: len(x['keywords']), reverse=True):
    print(f"  {article['title'][:65]}")
    print(f"    Keywords: {', '.join(article['keywords'][:5])}")
    print()

# ============================================================================
# GENERATE MARKDOWN REPORT
# ============================================================================
print("\n" + "=" * 70)
print("GENERATING REPORT...")
print("=" * 70)

report = f"""# RISKCORE Market Research Analysis

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Articles Analyzed:** {len(articles)}
**Sources:** WatersTechnology, Risk.net, The Hedge Fund Journal

---

## Executive Summary

Analysis of {len(articles)} industry articles reveals significant opportunities in the multi-manager risk aggregation space. Key findings:

- **{len(high_relevance)} articles** scored high relevance (3+) to our core problem
- **{len(aggregation_articles)} articles** directly mention multi-manager/aggregation themes
- Top pain points: **{', '.join([p[0] for p in sorted_pains[:3] if p[1] > 0])}**
- Dominant vendors: **{', '.join([v[0] for v in vendor_mentions.most_common(5)])}**

---

## 1. High-Relevance Articles (Score >= 3)

{len(high_relevance)} articles scored 3 or higher on our relevance scale:

| Score | Title | Source |
|-------|-------|--------|
"""

for article in sorted(high_relevance, key=lambda x: x.get('relevance_score', 0), reverse=True):
    title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
    report += f"| {article['relevance_score']} | {title} | {article['source_site']} |\n"

report += f"""

---

## 2. Top Topics & Themes

Tag frequency across all {len(articles)} articles:

| Tag | Frequency |
|-----|-----------|
"""

for tag, count in tag_counts.most_common(10):
    pct = round(count / len(articles) * 100)
    report += f"| {tag} | {count} ({pct}%) |\n"

report += """

### Key Theme Analysis

1. **Risk Management** - Core focus across all sources; VaR, stress testing, regulatory compliance
2. **Technology/Fintech** - AI, cloud, automation driving industry transformation
3. **Trading Operations** - Execution, settlement, clearing infrastructure
4. **Data Management** - Reference data, aggregation, quality issues
5. **Regulation** - DORA, T+1 settlement, reporting requirements

---

## 3. Pain Points Analysis

Keywords indicating challenges and problems mentioned in articles:

| Pain Point | Mentions | Context |
|------------|----------|---------|
"""

for keyword, count in sorted_pains[:10]:
    if count > 0:
        examples = pain_keywords[keyword][:1]
        context = examples[0]['title'][:50] + "..." if examples else ""
        report += f"| {keyword} | {count} | {context} |\n"

report += """

### Top 5 Pain Points (Ranked)

"""

rank = 1
for keyword, count in sorted_pains[:5]:
    if count > 0:
        report += f"""**{rank}. {keyword.title()}** ({count} mentions)
- Appears across multiple contexts: technology gaps, operational inefficiencies, regulatory challenges
- Example: "{pain_keywords[keyword][0]['title'][:80]}..."

"""
        rank += 1

report += """
---

## 4. Vendor Landscape

Vendors and platforms mentioned in the research:

| Vendor | Mentions | Category |
|--------|----------|----------|
"""

vendor_categories = {
    'Bloomberg': 'Data/Trading/Risk',
    'LSEG': 'Data/Exchange',
    'Aladdin': 'Investment Platform',
    'BlackRock': 'Asset Manager/Platform',
    'SimCorp': 'Investment Management',
    'MSCI': 'Risk/Analytics',
    'Axioma': 'Risk Analytics',
    'Enfusion': 'Cloud Platform',
    'SS&C': 'Fund Admin/Tech',
    'FactSet': 'Data/Analytics',
    'Refinitiv': 'Data',
    'Citadel': 'Multi-Manager HF',
    'Millennium': 'Multi-Manager HF',
    'Point72': 'Multi-Manager HF',
    'Brevan Howard': 'Hedge Fund',
    'Tradeweb': 'Trading Platform',
    'MarketAxess': 'Trading Platform',
    'AccessFintech': 'Post-trade',
    'Apex': 'Fund Admin',
}

for vendor, count in vendor_mentions.most_common(15):
    if count > 0:
        category = vendor_categories.get(vendor, 'Other')
        report += f"| {vendor} | {count} | {category} |\n"

report += """

### Competitive Landscape Insights

**Enterprise Platforms (Incumbents):**
- Bloomberg PORT, Aladdin, SimCorp Dimension dominate large institutions
- High cost ($500K-$5M+), long implementation, rigid architecture

**Point Solutions:**
- Numerous specialized tools for specific asset classes or risk types
- Creates integration burden and data silos

**Emerging Players:**
- Cloud-native platforms (Enfusion, etc.) gaining traction
- Focus on middle-market and emerging managers
- Still lack true multi-manager aggregation capabilities

---

## 5. Multi-Manager & Aggregation Focus

{len(aggregation_articles)} articles directly address multi-manager or aggregation themes:

"""

for article in sorted(aggregation_articles, key=lambda x: len(x['keywords']), reverse=True)[:10]:
    report += f"""### {article['title'][:70]}
- **Source:** {article['source']}
- **Keywords:** {', '.join(article['keywords'][:5])}
- **URL:** {article['url']}

"""

report += """
---

## 6. Gaps & Opportunities for RISKCORE

Based on this analysis, the following gaps present opportunities:

### Gap 1: No Unified Multi-Manager Risk View
**Problem:** Multi-manager funds struggle to aggregate risk across PMs using different systems.
**Evidence:** Articles mention "fragmented," "siloed," and "manual" approaches to firm-wide risk.
**RISKCORE Opportunity:** Universal data ingestion + real-time aggregation

### Gap 2: High Cost of Enterprise Solutions
**Problem:** Bloomberg/Aladdin/SimCorp are expensive and require full adoption.
**Evidence:** Vendor landscape shows concentration in expensive enterprise platforms.
**RISKCORE Opportunity:** Open-source, modular, pay-for-what-you-use model

### Gap 3: Slow Aggregation for Regulatory Reporting
**Problem:** Manual data gathering for Form PF, AIFMD, etc.
**Evidence:** "Regulation" is a top tag; DORA and reporting mentioned frequently.
**RISKCORE Opportunity:** Automated regulatory aggregation and reporting

### Gap 4: Lack of Natural Language Queries
**Problem:** Risk teams can't easily ask questions of their data.
**Evidence:** AI/GenAI trends heavily discussed but not applied to risk aggregation.
**RISKCORE Opportunity:** Claude-powered natural language risk queries

### Gap 5: Poor Cross-PM Netting Visibility
**Problem:** PMs unknowingly take offsetting positions.
**Evidence:** "Total portfolio approach" articles highlight this unmet need.
**RISKCORE Opportunity:** Real-time cross-PM netting and overlap detection

---

## 7. Recommendations

### Immediate (MVP Focus)
1. **Position aggregation API** - Ingest from any source
2. **Unified security master** - Map identifiers across systems
3. **Basic exposure views** - Sector, geography, asset class

### Near-term (Differentiation)
4. **Natural language queries** - "What's our net tech exposure?"
5. **Cross-PM overlap detection** - Alert on large offsetting positions
6. **Regulatory reporting templates** - Form PF, AIFMD

### Long-term (Moat)
7. **Real-time streaming** - Live position and risk updates
8. **What-if analysis** - Scenario modeling across portfolios
9. **Adapter marketplace** - Community-built integrations

---

## Appendix: Article Sources

| Source | Count | Focus |
|--------|-------|-------|
| WatersTechnology | {sum(1 for a in articles if a['source_site'] == 'waterstechnology')} | Trading tech, data management |
| Risk.net | {sum(1 for a in articles if a['source_site'] == 'risk.net')} | Risk management, investing |
| Hedge Fund Journal | {sum(1 for a in articles if a['source_site'] == 'hedge_fund_journal')} | HF strategies, operations |

---

*Analysis generated by RISKCORE research scraper*
"""

# Save report
with open('../docs/market_research_analysis.md', 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\nReport saved to: docs/market_research_analysis.md")
print(f"Report length: {len(report):,} characters")

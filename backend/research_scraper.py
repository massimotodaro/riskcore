"""
RISKCORE Research Scraper
Scrapes financial technology and risk management articles for market research.
"""

import os
import re
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client
from dateutil import parser as date_parser

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Keywords for relevance scoring
HIGH_RELEVANCE_KEYWORDS = [
    "multi-manager", "multi-strategy", "risk aggregation", "firm-wide risk",
    "cross-pm", "portfolio aggregation", "position aggregation", "ibor",
    "investment book of record", "risk consolidation", "enterprise risk"
]

MEDIUM_RELEVANCE_KEYWORDS = [
    "hedge fund risk", "portfolio risk", "risk management", "var",
    "value at risk", "exposure management", "risk technology", "risktech",
    "risk analytics", "prime broker", "multi-asset", "fund administrator"
]

LOW_RELEVANCE_KEYWORDS = [
    "hedge fund", "asset manager", "buy-side", "portfolio", "risk",
    "trading", "operations", "data management", "fintech"
]

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Article:
    source_site: str
    url: str
    title: str
    date_published: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    full_text: Optional[str] = None
    tags: list = field(default_factory=list)
    relevance_score: int = 1
    is_paywalled: bool = False

    def to_dict(self) -> dict:
        return {
            "source_site": self.source_site,
            "url": self.url,
            "title": self.title,
            "date_published": self.date_published,
            "author": self.author,
            "summary": self.summary[:500] if self.summary else None,
            "full_text": self.full_text,
            "tags": self.tags,
            "relevance_score": self.relevance_score,
            "is_paywalled": self.is_paywalled,
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_relevance(text: str) -> int:
    """Calculate relevance score 1-5 based on keyword presence."""
    if not text:
        return 1

    text_lower = text.lower()
    score = 1

    # High relevance keywords (+2 each, max contribution 4)
    high_matches = sum(1 for kw in HIGH_RELEVANCE_KEYWORDS if kw in text_lower)
    if high_matches >= 2:
        score += 4
    elif high_matches == 1:
        score += 2

    # Medium relevance keywords (+1 each, max contribution 2)
    if score < 5:
        medium_matches = sum(1 for kw in MEDIUM_RELEVANCE_KEYWORDS if kw in text_lower)
        if medium_matches >= 3:
            score += 2
        elif medium_matches >= 1:
            score += 1

    # Low relevance keywords (+0.5 each, max contribution 1)
    if score < 5:
        low_matches = sum(1 for kw in LOW_RELEVANCE_KEYWORDS if kw in text_lower)
        if low_matches >= 4:
            score += 1

    return min(score, 5)


def extract_tags(text: str) -> list:
    """Extract relevant topic tags from text."""
    if not text:
        return []

    text_lower = text.lower()
    tags = []

    tag_keywords = {
        "risk-management": ["risk management", "risk analytics", "var", "value at risk"],
        "multi-manager": ["multi-manager", "multi-strategy", "multi-pm"],
        "hedge-fund": ["hedge fund", "hedgefund"],
        "data-management": ["data management", "data aggregation", "ibor"],
        "technology": ["technology", "fintech", "risktech", "regtech"],
        "operations": ["operations", "operational", "middle office", "back office"],
        "regulation": ["regulation", "compliance", "regulatory", "sec", "cftc"],
        "trading": ["trading", "execution", "order management"],
        "portfolio": ["portfolio", "position", "exposure"],
        "prime-brokerage": ["prime broker", "prime brokerage", "pb"],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)

    return tags[:10]  # Max 10 tags


def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?\'"()-]', '', text)
    return text.strip()


def parse_date(date_str: str) -> Optional[str]:
    """Parse date string to ISO format."""
    if not date_str:
        return None
    try:
        parsed = date_parser.parse(date_str, fuzzy=True)
        return parsed.strftime("%Y-%m-%d")
    except:
        return None


def rate_limit_request(last_request_time: float, min_delay: float = 2.0) -> float:
    """Ensure minimum delay between requests."""
    elapsed = time.time() - last_request_time
    if elapsed < min_delay:
        time.sleep(min_delay - elapsed)
    return time.time()


# ============================================================================
# SCRAPER CLASSES
# ============================================================================

class BaseScraper:
    """Base class for article scrapers."""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.last_request = 0
        self.articles = []

    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL with rate limiting."""
        self.last_request = rate_limit_request(self.last_request)
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            return None

    def scrape(self, max_articles: int) -> list:
        """Override in subclass."""
        raise NotImplementedError


class WatersTechnologyScraper(BaseScraper):
    """Scraper for WatersTechnology.com"""

    def __init__(self):
        super().__init__("waterstechnology")
        self.base_url = "https://www.waterstechnology.com"
        self.sections = [
            "/trading-tech",
            "/data-management",
            "/buy-side-technology",
        ]

    def scrape(self, max_articles: int = 25) -> list:
        print(f"\nScraping WatersTechnology ({max_articles} articles)...")
        articles = []
        seen_urls = set()

        for section in self.sections:
            if len(articles) >= max_articles:
                break

            url = self.base_url + section
            print(f"  Fetching section: {section}")
            soup = self.fetch(url)

            if not soup:
                continue

            # Find article links
            article_links = soup.select('article a[href*="/"], .article-card a[href*="/"]')

            for link in article_links:
                if len(articles) >= max_articles:
                    break

                href = link.get('href', '')
                if not href or href in seen_urls:
                    continue

                # Skip non-article links
                if any(x in href for x in ['/author/', '/topic/', '/sponsored', '/video']):
                    continue

                article_url = urljoin(self.base_url, href)
                seen_urls.add(href)

                article = self.scrape_article(article_url)
                if article:
                    articles.append(article)
                    print(f"    Scraped: {article.title[:60]}...")

        return articles

    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article."""
        soup = self.fetch(url)
        if not soup:
            return None

        # Title
        title_el = soup.select_one('h1, .article-title')
        title = clean_text(title_el.get_text()) if title_el else "Unknown Title"

        # Check for paywall
        paywall_indicators = soup.select('.paywall, .subscription-required, .premium-content')
        is_paywalled = len(paywall_indicators) > 0 or "Subscribe" in str(soup)[:5000]

        # Date
        date_el = soup.select_one('time, .article-date, [datetime]')
        date_str = None
        if date_el:
            date_str = date_el.get('datetime') or date_el.get_text()
        date_published = parse_date(date_str)

        # Author
        author_el = soup.select_one('.author-name, [rel="author"], .byline')
        author = clean_text(author_el.get_text()) if author_el else None

        # Summary - meta description or first paragraph
        meta_desc = soup.select_one('meta[name="description"]')
        summary = meta_desc.get('content') if meta_desc else None

        if not summary:
            first_p = soup.select_one('article p, .article-body p')
            summary = clean_text(first_p.get_text()) if first_p else None

        # Full text (if not paywalled)
        full_text = None
        if not is_paywalled:
            article_body = soup.select_one('article, .article-body, .article-content')
            if article_body:
                paragraphs = article_body.select('p')
                full_text = ' '.join(clean_text(p.get_text()) for p in paragraphs)

        # Calculate relevance and tags
        content = f"{title} {summary or ''} {full_text or ''}"
        relevance = calculate_relevance(content)
        tags = extract_tags(content)

        return Article(
            source_site=self.source_name,
            url=url,
            title=title,
            date_published=date_published,
            author=author,
            summary=summary,
            full_text=full_text,
            tags=tags,
            relevance_score=relevance,
            is_paywalled=is_paywalled
        )


class RiskNetScraper(BaseScraper):
    """Scraper for Risk.net"""

    def __init__(self):
        super().__init__("risk.net")
        self.base_url = "https://www.risk.net"
        self.sections = [
            "/risk-management",
            "/investing",
            "/hedge-funds",
        ]

    def scrape(self, max_articles: int = 25) -> list:
        print(f"\nScraping Risk.net ({max_articles} articles)...")
        articles = []
        seen_urls = set()

        for section in self.sections:
            if len(articles) >= max_articles:
                break

            url = self.base_url + section
            print(f"  Fetching section: {section}")
            soup = self.fetch(url)

            if not soup:
                continue

            # Find article links
            article_links = soup.select('a[href*="/"]')

            for link in article_links:
                if len(articles) >= max_articles:
                    break

                href = link.get('href', '')

                # Only get article-like URLs (typically have dates or numeric IDs)
                if not href or href in seen_urls:
                    continue
                if any(x in href for x in ['/author/', '/topic/', '/sponsored', '/video', '/search']):
                    continue
                if not re.search(r'/\d{4,}|/20\d{2}/', href):
                    continue

                article_url = urljoin(self.base_url, href) if not href.startswith('http') else href
                seen_urls.add(href)

                article = self.scrape_article(article_url)
                if article:
                    articles.append(article)
                    print(f"    Scraped: {article.title[:60]}...")

        return articles

    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article."""
        soup = self.fetch(url)
        if not soup:
            return None

        # Title
        title_el = soup.select_one('h1')
        title = clean_text(title_el.get_text()) if title_el else "Unknown Title"

        if len(title) < 10:
            return None

        # Risk.net is heavily paywalled
        is_paywalled = True

        # Date
        date_el = soup.select_one('time, .date, [datetime]')
        date_str = None
        if date_el:
            date_str = date_el.get('datetime') or date_el.get_text()
        date_published = parse_date(date_str)

        # Author
        author_el = soup.select_one('.author, [rel="author"], .byline')
        author = clean_text(author_el.get_text()) if author_el else None

        # Summary only (paywalled)
        meta_desc = soup.select_one('meta[name="description"]')
        summary = meta_desc.get('content') if meta_desc else None

        if not summary:
            first_p = soup.select_one('article p, .article-body p, .standfirst')
            summary = clean_text(first_p.get_text()) if first_p else None

        content = f"{title} {summary or ''}"
        relevance = calculate_relevance(content)
        tags = extract_tags(content)

        return Article(
            source_site=self.source_name,
            url=url,
            title=title,
            date_published=date_published,
            author=author,
            summary=summary,
            full_text=None,
            tags=tags,
            relevance_score=relevance,
            is_paywalled=is_paywalled
        )


class FINalternativesScraper(BaseScraper):
    """Scraper for FINalternatives.com - hedge fund industry news"""

    def __init__(self):
        super().__init__("finalternatives")
        self.base_url = "https://www.finalternatives.com"

    def scrape(self, max_articles: int = 15) -> list:
        print(f"\nScraping FINalternatives ({max_articles} articles)...")
        articles = []
        seen_urls = set()

        # Try main news page
        print(f"  Fetching: {self.base_url}")
        soup = self.fetch(self.base_url)

        if not soup:
            return articles

        # Find article links
        article_links = soup.select('a[href*="/"]')

        for link in article_links:
            if len(articles) >= max_articles:
                break

            href = link.get('href', '')
            if not href or href in seen_urls:
                continue

            # Look for article-like URLs
            if any(x in href.lower() for x in ['/category/', '/tag/', '/page/', '/author/', 'subscribe', 'login', 'contact']):
                continue

            # Must be a substantial path (likely an article)
            if href.count('/') < 2 and not re.search(r'/\d+/', href):
                continue

            article_url = urljoin(self.base_url, href) if not href.startswith('http') else href

            if 'finalternatives.com' not in article_url:
                continue

            seen_urls.add(href)

            article = self.scrape_article(article_url)
            if article and len(article.title) > 20:
                articles.append(article)
                print(f"    Scraped: {article.title[:60]}...")

        return articles

    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article."""
        soup = self.fetch(url)
        if not soup:
            return None

        title_el = soup.select_one('h1, .entry-title, .post-title')
        title = clean_text(title_el.get_text()) if title_el else None

        if not title or len(title) < 15:
            return None

        is_paywalled = False

        date_el = soup.select_one('time, .date, .entry-date, .published')
        date_str = date_el.get('datetime') or date_el.get_text() if date_el else None
        date_published = parse_date(date_str)

        author_el = soup.select_one('.author, .byline')
        author = clean_text(author_el.get_text()) if author_el else None

        meta_desc = soup.select_one('meta[name="description"]')
        summary = meta_desc.get('content') if meta_desc else None

        article_body = soup.select_one('article, .entry-content, .post-content')
        full_text = None
        if article_body:
            paragraphs = article_body.select('p')
            full_text = ' '.join(clean_text(p.get_text()) for p in paragraphs)
            if not summary and full_text:
                summary = full_text[:500]

        content = f"{title} {summary or ''} {full_text or ''}"
        relevance = calculate_relevance(content)
        tags = extract_tags(content)

        return Article(
            source_site=self.source_name,
            url=url,
            title=title,
            date_published=date_published,
            author=author,
            summary=summary,
            full_text=full_text,
            tags=tags,
            relevance_score=relevance,
            is_paywalled=is_paywalled
        )


class HedgeFundJournalScraper(BaseScraper):
    """Scraper for TheHedgeFundJournal.com"""

    def __init__(self):
        super().__init__("hedge_fund_journal")
        self.base_url = "https://thehedgefundjournal.com"

    def scrape(self, max_articles: int = 10) -> list:
        print(f"\nScraping The Hedge Fund Journal ({max_articles} articles)...")
        articles = []
        seen_urls = set()

        # Try specific article sections
        urls_to_try = [
            f"{self.base_url}/news",
            f"{self.base_url}/articles",
            self.base_url,
        ]

        for page_url in urls_to_try:
            if len(articles) >= max_articles:
                break

            print(f"  Fetching: {page_url}")
            soup = self.fetch(page_url)

            if not soup:
                continue

            # Look for article-specific links
            article_links = soup.select('a[href*="article"], a[href*="news"], a[href*="profile"], .article a, .post a')

            for link in article_links:
                if len(articles) >= max_articles:
                    break

                href = link.get('href', '')
                if not href or href in seen_urls:
                    continue
                if any(x in href.lower() for x in ['/tag/', '/category/', '/author/', '/page/', 'subscribe', 'login']):
                    continue

                article_url = urljoin(self.base_url, href)

                # Only process URLs from this domain
                if 'thehedgefundjournal.com' not in article_url:
                    continue

                seen_urls.add(href)

                article = self.scrape_article(article_url)
                if article and self._is_valid_article(article):
                    articles.append(article)
                    print(f"    Scraped: {article.title[:60]}...")

        return articles

    def _is_valid_article(self, article: Article) -> bool:
        """Filter out navigation pages and non-articles."""
        if not article.title or len(article.title) < 15:
            return False
        # Skip titles that look like navigation
        nav_patterns = ['subscribe', 'login', 'issue ', 'everything', 'contribute', 'become a']
        if any(p in article.title.lower() for p in nav_patterns):
            return False
        return True

    def scrape_article(self, url: str) -> Optional[Article]:
        """Scrape individual article."""
        soup = self.fetch(url)
        if not soup:
            return None

        title_el = soup.select_one('h1, .entry-title, .article-title')
        title = clean_text(title_el.get_text()) if title_el else None

        if not title or len(title) < 15:
            return None

        is_paywalled = False

        date_el = soup.select_one('time, .date, .entry-date, .published')
        date_str = date_el.get('datetime') or date_el.get_text() if date_el else None
        date_published = parse_date(date_str)

        author_el = soup.select_one('.author, .byline, .writer')
        author = clean_text(author_el.get_text()) if author_el else None

        meta_desc = soup.select_one('meta[name="description"]')
        summary = meta_desc.get('content') if meta_desc else None

        article_body = soup.select_one('article, .entry-content, .post-content, .article-body')
        full_text = None
        if article_body:
            paragraphs = article_body.select('p')
            full_text = ' '.join(clean_text(p.get_text()) for p in paragraphs)
            if not summary and full_text:
                summary = full_text[:500]

        content = f"{title} {summary or ''} {full_text or ''}"
        relevance = calculate_relevance(content)
        tags = extract_tags(content)

        return Article(
            source_site=self.source_name,
            url=url,
            title=title,
            date_published=date_published,
            author=author,
            summary=summary,
            full_text=full_text,
            tags=tags,
            relevance_score=relevance,
            is_paywalled=is_paywalled
        )


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def init_supabase() -> Optional[Client]:
    """Initialize Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return None

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        return None


def save_articles(client: Client, articles: list) -> dict:
    """Save articles to Supabase."""
    stats = {"inserted": 0, "skipped": 0, "errors": 0}

    for article in articles:
        try:
            data = article.to_dict()
            result = client.table("research_articles").upsert(
                data,
                on_conflict="url"
            ).execute()

            if result.data:
                stats["inserted"] += 1
            else:
                stats["skipped"] += 1
        except Exception as e:
            if "duplicate" in str(e).lower():
                stats["skipped"] += 1
            else:
                stats["errors"] += 1
                print(f"  Error saving article: {e}")

    return stats


def save_to_json(articles: list, filename: str = "research_articles.json"):
    """Save articles to JSON file as backup."""
    import json

    data = [a.to_dict() for a in articles]
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\nBackup saved to: {filepath}")
    return filepath


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("RISKCORE Research Scraper")
    print("=" * 60)

    all_articles = []

    # Initialize scrapers
    scrapers = [
        (WatersTechnologyScraper(), 25),
        (RiskNetScraper(), 25),
        (FINalternativesScraper(), 15),
        (HedgeFundJournalScraper(), 10),
    ]

    # Run scrapers
    for scraper, max_articles in scrapers:
        try:
            articles = scraper.scrape(max_articles)
            all_articles.extend(articles)
        except Exception as e:
            print(f"Error with {scraper.source_name}: {e}")

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)

    # Summary by source
    source_counts = {}
    relevance_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    paywalled_count = 0

    for article in all_articles:
        source_counts[article.source_site] = source_counts.get(article.source_site, 0) + 1
        relevance_counts[article.relevance_score] += 1
        if article.is_paywalled:
            paywalled_count += 1

    print(f"\nTotal articles scraped: {len(all_articles)}")
    print("\nBy source:")
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    print("\nBy relevance score:")
    for score in range(5, 0, -1):
        count = relevance_counts[score]
        bar = "#" * min(count, 40)
        print(f"  {score}: {bar} ({count})")

    print(f"\nPaywalled articles: {paywalled_count}")
    print(f"Full-text available: {len(all_articles) - paywalled_count}")

    # Save to JSON backup
    save_to_json(all_articles)

    # Save to Supabase
    print("\n" + "-" * 60)
    print("Saving to Supabase...")

    client = init_supabase()
    if client:
        stats = save_articles(client, all_articles)
        print(f"  Inserted: {stats['inserted']}")
        print(f"  Skipped (duplicates): {stats['skipped']}")
        print(f"  Errors: {stats['errors']}")
    else:
        print("  Skipped - Supabase not configured")
        print("  Set SUPABASE_URL and SUPABASE_KEY in backend/.env")

    # Show high-relevance articles
    high_relevance = [a for a in all_articles if a.relevance_score >= 4]
    if high_relevance:
        print("\n" + "=" * 60)
        print("HIGH RELEVANCE ARTICLES (score >= 4)")
        print("=" * 60)
        for article in high_relevance[:10]:
            print(f"\n[{article.relevance_score}] {article.title}")
            print(f"    Source: {article.source_site}")
            print(f"    URL: {article.url}")
            print(f"    Tags: {', '.join(article.tags)}")

    return all_articles


if __name__ == "__main__":
    main()

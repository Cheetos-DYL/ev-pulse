"""LLM-powered article filtering and categorization.

4-factor relevance scoring (0-100):
  - Keyword match (0-40): Explicit mention of EV charging terms
  - Market impact (0-30): Deal size, charger count, budget involved
  - Recency (0-20): Decay over 30 days
  - Source authority (0-10): Official govt/utility > local news > blog/social

Category priority rules (highest wins when multiple match):
  government_policy > ma_partnership > charger_install > charging_standards > grid_pricing > ev_sales_stats
"""

import os
import json
import logging
import re
from datetime import datetime, timezone

from .sources import CATEGORY_PRIORITY, CATEGORY_KEYWORDS, CATEGORY_NAMES

logger = logging.getLogger(__name__)

client = None


def get_client():
    global client
    if client is None:
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            logger.warning("No LLM API key found — using keyword-only scoring")
            return None
        # Use a simple dict as a pseudo-client — actual API calls use raw HTTP
        client = {"api_key": api_key, "base_url": os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')}
    return client


def llm_call(messages: list, model: str = None, temperature: float = 0.1, max_tokens: int = 300) -> str | None:
    """Make an LLM API call via raw HTTP, bypassing library compatibility issues."""
    c = get_client()
    if c is None or isinstance(c, dict) is False:
        return None
    try:
        import urllib.request
        import urllib.error
        url = f"{c['base_url'].rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model or os.getenv('LLM_MODEL', 'gpt-4o-mini'),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {c['api_key']}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=30)
        body = json.loads(resp.read())
        return body["choices"][0]["message"]["content"]
    except Exception as e:
        error_detail = f"{type(e).__name__}: {str(e)[:200]}"
        if hasattr(e, 'read'):
            try:
                error_detail += f" | body: {e.read()[:300]}"
            except Exception:
                pass
        logger.warning(f"LLM API call failed: {error_detail}")
        global _last_llm_error
        _last_llm_error = error_detail
        return None


_last_llm_error = ""


def get_last_llm_error():
    global _last_llm_error
    return _last_llm_error


# ─── 4-Factor Relevance Scoring (0-100) ───────────────────────────────

def compute_relevance_score(article: dict) -> float:
    """Compute a 4-factor relevance score (0-100):
    - Keyword match (0-40): How strongly the article matches EV charging keywords
    - Market impact (0-30): Scale of deal/installation/government action
    - Recency (0-20): Full score within 7 days, decays to 0 after 30
    - Source authority (0-10): Official/utility > news > blog
    """
    title = article.get('title', '')
    summary = article.get('summary', '')
    text = f"{title} {summary}".lower()
    source_name = article.get('source', '').lower()
    
    # 1. Keyword match (0-40)
    kw_score = _keyword_match_score(text, title.lower())
    
    # 2. Market impact (0-30)
    impact_score = _market_impact_score(text)
    
    # 3. Recency (0-20)
    recency_score = _recency_score(article)
    
    # 4. Source authority (0-10)
    authority_score = _source_authority_score(source_name)
    
    total = min(100, kw_score + impact_score + recency_score + authority_score)
    return max(0, total)


STRONG_KW = [
    "ev charging", "charging station", "charging infrastructure",
    "electric vehicle charging", "charging network", "charging tariff",
    "charging standard", "v2g", "ultra-fast charging", "fast charging",
    "ev policy", "ev incentive", "ev subsidy",
    "charging hub", "supercharger", "charging point",
]

MODERATE_KW = [
    "electric vehicle", "ev market", "ev adoption", "ev sales",
    "charging point", "ev infrastructure", "ev investment",
    "charger installation", "ev fleet",
]

HIGH_IMPACT_PATTERNS = [
    r'\$\d+[bmk]', r'\d+\s*billion', r'\d+\s*million',
    r'\d+,?\d*\s*(charging|charger|station)s?',
    r'\d+,?\d*\s*(EV|electric)\s*(vehicle|car)s?',
    r'investment of', r'funding of',
]


def _keyword_match_score(text: str, title: str) -> float:
    """Score 0-40 based on keyword presence."""
    score = 0.0
    
    for kw in STRONG_KW:
        if kw in text:
            score += 4.0
        if kw in title:
            score += 2.0  # title bonus
    
    for kw in MODERATE_KW:
        if kw in text:
            score += 2.0
        if kw in title:
            score += 1.0
    
    for kw in [
        "battery mining", "lithium mining", "cobalt mining",
        "autonomous driving", "self-driving",
        "battery technology", "solid state battery",
    ]:
        if kw in text:
            score -= 3.0
    
    return max(0, min(40, score))


def _market_impact_score(text: str) -> float:
    """Score 0-30 based on deal size, charger count, government action indicators."""
    score = 0.0
    
    for pattern in HIGH_IMPACT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 10.0
    
    # Government action signals = high impact
    gov_signals = [
        "government", "ministry", "announced", "launch", "plan to",
        "new policy", "regulation", "mandate", "investment",
    ]
    for kw in gov_signals:
        if kw in text:
            score += 3.0
            break  # one government signal is enough
    
    # Partnership/M&A signals
    partnership_signals = [
        "partnership", "acquisition", "joint venture", "collaboration",
        "memorandum of understanding", "mou", "signed an agreement",
    ]
    for kw in partnership_signals:
        if kw in text:
            score += 4.0
            break
    
    return max(0, min(30, score))


def _recency_score(article: dict) -> float:
    """Score 0-20 based on recency. Full score within 7 days, decays to 0 after 30."""
    published = article.get('published_at') or article.get('collected_at')
    if not published:
        # If no date, assume somewhat recent (score 10)
        return 10.0
    
    try:
        if isinstance(published, str):
            # Handle various date formats
            published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
        else:
            published_dt = published
        
        now = datetime.now(timezone.utc)
        days_old = (now - published_dt).total_seconds() / 86400.0
        
        if days_old <= 7:
            return 20.0  # Full score
        elif days_old <= 14:
            return 15.0
        elif days_old <= 21:
            return 10.0
        elif days_old <= 30:
            return 5.0
        else:
            return 0.0
    except (ValueError, TypeError):
        return 10.0  # Default moderately recent


AUTHORITY_MAP = [
    # (keyword in source name, score)
    ("gov", 10), ("government", 10), ("ministry", 10),
    ("energy", 9), ("utility", 9), ("power", 9),
    ("연합뉴스", 8), ("한국경제", 8), ("한겨레", 8), ("전자신문", 8),
    ("nikkei", 9), ("japan times", 8),
    ("reuters", 9), ("bloomberg", 9),
    ("al jazeera", 8), ("arab news", 8), ("gulf news", 8),
    ("abc news", 8), ("cna", 8), ("straits times", 8),
    ("bangkok post", 7), ("the star", 7),
    ("g1", 7), ("uol", 7),
    ("news24", 7), ("business day", 7),
    ("expansión", 7), ("el financiero", 7),
    ("google news", 5),  # Aggregator
]


def _source_authority_score(source_name: str) -> float:
    """Score 0-10 based on source authority."""
    source_lower = source_name.lower()
    for keyword, score in AUTHORITY_MAP:
        if keyword in source_lower:
            return float(score)
    return 5.0  # Default: standard news


# ─── Category Assignment ─────────────────────────────────────────

def assign_category(article: dict) -> str:
    """Assign primary category using priority rules.
    
    Checks each category's keywords against the article text.
    First matching category (highest priority) wins.
    Falls back to 'other' if no categories match.
    """
    text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
    
    for category in CATEGORY_PRIORITY:
        keywords = CATEGORY_KEYWORDS.get(category, [])
        for kw in keywords:
            if kw.lower() in text:
                return category
    
    return "other"


# ─── LLM Analysis ───────────────────────────────────────────────

def keyword_score(article: dict) -> float:
    """Quick keyword-based relevance score (0-10) — kept for backward compat."""
    text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
    score = 0.0

    for kw in STRONG_KW:
        if kw in text:
            score += 2.0
        if kw in title if (title := article.get('title', '')).lower() else False:
            score += 1.0

    for kw in MODERATE_KW:
        if kw in text:
            score += 1.0

    for kw in [
        "battery mining", "lithium mining", "cobalt mining",
        "autonomous driving", "self-driving",
    ]:
        if kw in text:
            score -= 2.0

    return max(0, min(10, score))


def llm_analyze_article(article: dict) -> dict:
    """Use LLM to analyze and categorize an article."""
    try:
        c = get_client()
    except Exception as e:
        logger.warning(f"LLM client creation failed: {e}")
        return _fallback_analysis(article)
    if c is None:
        return _fallback_analysis(article)

    # Build categories description for LLM
    cat_descriptions = "\n".join([
        f"- {cat}: {CATEGORY_NAMES.get(cat, cat)}"
        for cat in CATEGORY_PRIORITY
    ])

    prompt = f"""Analyze this news article for EV charging relevance.

Title: {article.get('title', '')}
Summary: {article.get('summary', '')}
Region: {article.get('region', '')}
Language: {article.get('language', 'en')}

Return JSON with:
- relevance_score: 0-100 (use the 4-factor model: keyword match, market impact, recency, source authority)
- category: one of the following categories (select the best SINGLE category):
{cat_descriptions}
- tags: array of 2-5 relevant tags
- one_line_summary: English one-line summary starting with "Why it matters: "
- translated_title: if the original title is not in English, provide an English translation; otherwise same as title
- keywords: array of 3-7 key terms/entities extracted from the article
- why_it_matters: a short 1-sentence explanation of why this article is significant (just the reason, no prefix)

If the article is in a non-English language (Korean, Japanese, Chinese, Portuguese, Spanish, Arabic, etc.):
1. First detect the language
2. Translate the title and key content to English
3. Then analyze relevance as usual
4. Extract keywords from the ORIGINAL language text, keep them in their original form

Return ONLY valid JSON, no markdown."""

    try:
        response_text = llm_call(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400
        )
        if response_text is None:
            logger.warning(f"LLM call returned None for article {article.get('id', '?')} — fallback")
            return _fallback_analysis(article)
        result = json.loads(response_text)
        article['relevance_score'] = result.get('relevance_score', 0)
        article['category'] = result.get('category', 'other')
        article['tags'] = result.get('tags', [])
        article['translated_title'] = result.get('translated_title', '')
        article['summary'] = result.get('one_line_summary', article.get('summary', ''))
        article['keywords'] = result.get('keywords', [])
        article['why_it_matters'] = result.get('why_it_matters', '')
        article['analyzed'] = 1
        return article
    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}")
        return _fallback_analysis(article)


def _extract_keywords_fallback(article: dict) -> list[str]:
    """Extract keywords from article title and summary without LLM."""
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('source', '')}".lower()
    
    # Known EV charging keywords to extract
    known_terms = [
        "ev charging", "electric vehicle", "charging station", "charging point",
        "charging network", "charging infrastructure", "fast charging", "ultra-fast",
        "charging hub", "supercharger", "charging tariff", "charging cost",
        "v2g", "vehicle-to-grid", "smart charging", "bidirectional charging",
        "nacs", "ccs", "chademo", "charging standard",
        "subsidy", "incentive", "government policy", "regulation",
        "partnership", "investment", "joint venture", "funding",
        "ev sales", "ev adoption", "market share", "ev registration",
        "renewable energy", "solar charging", "grid integration",
        "battery swapping", "charging app", "roaming",
    ]
    
    # Also extract region/country names
    regions = {
        "korea", "south korea", "seoul", "한국", "전기차",
        "uae", "dubai", "abu dhabi", "middle east",
        "japan", "tokyo", "充電", "ev充電",
        "australia", "sydney", "melbourne",
        "taiwan", "taipei", "台灣", "電動車",
        "brazil", "brasil", "sao paulo", "veículo elétrico",
        "mexico", "méxico", "mexico city", "vehículo eléctrico",
        "africa", "south africa", "kenya", "nigeria",
        "southeast asia", "singapore", "thailand", "indonesia", "vietnam", "malaysia",
        "china", "europe", "us", "united states",
    }
    
    found = []
    for term in known_terms:
        if term in text:
            found.append(term)
    
    for region in regions:
        if region in text:
            found.append(region)
    
    # Deduplicate and limit
    seen = set()
    unique = []
    for kw in found:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    
    return unique[:10]


def _fallback_analysis(article: dict) -> dict:
    """Keyword-only fallback when LLM is unavailable."""
    article['relevance_score'] = compute_relevance_score(article)
    article['category'] = assign_category(article)
    article['tags'] = []
    article['keywords'] = _extract_keywords_fallback(article)
    article['analyzed'] = 1
    
    # Generate meaningful "why it matters" text from category + region
    cat = article['category']
    region_name = article.get('region', 'this market')
    source = article.get('source', '')
    title = article.get('title', '')
    
    WHY_TEMPLATES = {
        "government_policy": f"Policy change affecting EV charging in {region_name}",
        "ma_partnership": f"{source} deal signals market movement in {region_name}" if source else f"Market development in {region_name}",
        "charger_install": f"{source} expanding charging infrastructure in {region_name}" if source else f"Charging infrastructure update for {region_name}",
        "charging_standards": f"Charging standard development affecting {region_name}",
        "grid_pricing": f"Grid or pricing update affecting EV charging in {region_name}",
        "ev_sales_stats": f"EV market data for {region_name}",
    }
    
    article['why_it_matters'] = WHY_TEMPLATES.get(cat, f"EV charging development in {region_name}")
    
    # Generate a short summary from the title if none exists
    if not article.get('summary'):
        article['summary'] = title[:200]
    
    return article


def batch_analyze(articles: list[dict], use_llm: bool = True) -> list[dict]:
    """Analyze a batch of articles. Keyword score first, LLM for promising ones."""
    analyzed = []
    for article in articles:
        # Quick keyword score (backward compat threshold)
        kw_score = keyword_score(article)
        article['relevance_score'] = kw_score

        # Use new scoring as primary, or LLM for deeper analysis
        if use_llm and kw_score >= 2:
            article = llm_analyze_article(article)
        else:
            article = _fallback_analysis(article)

        analyzed.append(article)

    return analyzed

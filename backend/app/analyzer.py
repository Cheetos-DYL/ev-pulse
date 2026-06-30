"""LLM-powered article filtering and categorization."""

import os
import json
import logging

from .sources import CATEGORIES

logger = logging.getLogger(__name__)

client = None


def get_client():
    global client
    if client is None:
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
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


def keyword_score(article: dict) -> float:
    """Quick keyword-based relevance score (0-10)."""
    text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
    score = 0.0

    # Strong EV keywords = high score
    strong_keywords = [
        "ev charging", "charging station", "charging infrastructure",
        "electric vehicle charging", "charging network", "charging tariff",
        "charging standard", "v2g", "ultra-fast charging", "fast charging",
        "ev policy", "ev incentive", "ev subsidy",
    ]

    # Moderate keywords = medium score
    moderate_keywords = [
        "electric vehicle", "ev market", "ev adoption", "ev sales",
        "charging point", "ev infrastructure", "ev investment",
    ]

    # Negative keywords = reduce score
    negative_keywords = [
        "battery mining", "lithium mining", "cobalt mining",
        "autonomous driving", "self-driving",
    ]

    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()

    for kw in strong_keywords:
        if kw in text:
            score += 2.0
        if kw in title:
            score += 1.0  # Title bonus

    for kw in moderate_keywords:
        if kw in text:
            score += 1.0

    for kw in negative_keywords:
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

    prompt = f"""Analyze this news article for EV charging relevance.

Title: {article.get('title', '')}
Summary: {article.get('summary', '')}
Region: {article.get('region', '')}
Language: {article.get('language', 'en')}

Return JSON with:
- relevance_score: 0-10 (10 = highly relevant to EV charging services/trends/policy)
- category: one of "service", "trend", "policy", "other"
- tags: array of 2-5 relevant tags
- one_line_summary: English one-line summary
- translated_title: if the original title is not in English, provide an English translation; otherwise same as title

If the article is in a non-English language (Korean, Japanese, Chinese, Portuguese, Spanish, Arabic, etc.):
1. First detect the language
2. Translate the title and key content to English
3. Then analyze relevance as usual

Categories:
- service: charging networks, operators, pricing, new services
- trend: market data, adoption rates, infrastructure stats
- policy: regulations, incentives, standards, government actions
- other: tangentially related

Return ONLY valid JSON, no markdown."""

    try:
        response_text = llm_call(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        if response_text is None:
            logger.warning(f"LLM call returned None for article {article.get('id', '?')} — fallback")
            return _fallback_analysis(article)
        result = json.loads(response_text)
        article['relevance_score'] = result.get('relevance_score', 0)
        article['category'] = result.get('category', 'other')
        article['tags'] = result.get('tags', [])
        article['title'] = result.get('translated_title', article.get('title', ''))
        article['summary'] = result.get('one_line_summary', article.get('summary', ''))
        article['analyzed'] = 1
        return article
    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}")
        return _fallback_analysis(article)


def _fallback_analysis(article: dict) -> dict:
    """Keyword-only fallback when LLM is unavailable."""
    article['relevance_score'] = keyword_score(article)
    article['category'] = 'other'
    article['tags'] = []
    article['analyzed'] = 1
    return article


def batch_analyze(articles: list[dict], use_llm: bool = True) -> list[dict]:
    """Analyze a batch of articles. Keyword score first, LLM for promising ones."""
    analyzed = []
    for article in articles:
        # Quick keyword filter
        kw_score = keyword_score(article)
        article['relevance_score'] = kw_score

        if kw_score < 2:
            article['analyzed'] = 1
            analyzed.append(article)
            continue

        if use_llm:
            article = llm_analyze_article(article)
        else:
            article = _fallback_analysis(article)

        analyzed.append(article)

    return analyzed

"""RSS feed scraper with local-language support.

Collects from region-specific RSS feeds (including local-language sources)
and Google News RSS with language-specific queries.
"""

import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

from .sources import SOURCES

logger = logging.getLogger(__name__)


def _is_ev_related(title: str, summary: str, language: str = "en") -> bool:
    """Strict EV relevance check — requires strong signal."""
    text = f"{title} {summary}".lower()
    
    # Strong EV keywords (high confidence)
    strong_ev = {
        "en": ["ev charging", "electric vehicle", "charging station", "charging network",
               "fast charging", "ev infrastructure", "charging tariff", "charging point",
               "v2g", "ev policy", "ev subsidy", "charging hub", "charging standard",
               "ultra-fast", "supercharger", "ev adoption", "ev market"],
        "ko": ["전기차 충전", "충전소", "전기자동차", "충전 인프라", "급속 충전",
               "ev 충전", "전기차 보조금", "충전기 설치"],
        "ja": ["EV充電", "充電スタンド", "急速充電", "充電インフラ", "充電ネットワーク",
               "電気自動車充電", "スーパーチャージャー"],
        "zh": ["電動車充電", "充電站", "充電樁", "充電基礎設施", "快速充電"],
        "pt": ["carregamento elétrico", "estação de carga", "carro elétrico", "veículo elétrico",
               "recarga elétrica", "mobilidade elétrica", "infraestrutura de carga"],
        "es": ["estación de carga", "vehículo eléctrico", "carga eléctrica", "punto de recarga",
               "movilidad eléctrica", "infraestructura de carga", "coche eléctrico"],
        "ar": ["شحن السيارات", "محطة شحن", "سيارة كهربائية", "شحن كهربائي"],
    }
    
    lang_code = language if language in strong_ev else "en"
    keywords = strong_ev[lang_code]
    
    # Must match at least one strong keyword
    for kw in keywords:
        if kw.lower() in text:
            return True
    
    # Also check English keywords for mixed-language articles
    for kw in strong_ev["en"]:
        if kw.lower() in text:
            return True
    
    return False


def _get_google_news_rss(query: str, language: str = "en", country: str = "US") -> list[dict]:
    """Fetch articles from Google News RSS with language support."""
    articles = []
    encoded_query = query.replace(' ', '+')
    
    # Map language to Google hl parameter
    hl_map = {"ko": "ko", "ja": "ja", "zh": "zh-TW", "pt": "pt", "es": "es",
              "ar": "ar", "vi": "vi", "en": "en-US"}
    gl_map = {"ko": "KR", "ja": "JP", "zh": "TW", "pt": "BR", "es": "MX",
              "ar": "AE", "vi": "VN", "en": "US"}
    
    hl = hl_map.get(language, "en-US")
    gl = gl_map.get(language, "US")
    
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={gl}:{hl.split('-')[0]}"
    
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            
            if not title or not link:
                continue
            
            summary = ''
            if hasattr(entry, 'summary'):
                summary = BeautifulSoup(entry.summary, 'html.parser').get_text()[:500]
            
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            
            articles.append({
                'title': title,
                'url': link,
                'source': 'Google News',
                'language': language,
                'summary': summary,
                'published_at': published,
            })
    except Exception as e:
        logger.warning(f"Failed to fetch Google News ({language}): {e}")
    
    return articles


def collect_from_rss(region: str) -> list[dict]:
    """Collect EV-related articles from a region, including local-language sources."""
    articles = []
    source_config = SOURCES.get(region, {})
    feeds = source_config.get("feeds", [])
    region_lang = source_config.get("language", "en")
    
    # 1. Try region-specific RSS feeds (local-language + English)
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            feed_lang = feed_info.get("language", "en")
            for entry in feed.entries[:30]:
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                
                if not title or not link:
                    continue
                
                summary = ''
                if hasattr(entry, 'summary'):
                    summary = BeautifulSoup(entry.summary, 'html.parser').get_text()[:500]
                
                # Use feed language for keyword matching
                if _is_ev_related(title, summary, feed_lang):
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6]).isoformat()
                    
                    articles.append({
                        'title': title,
                        'url': link,
                        'source': feed_info["name"],
                        'region': region,
                        'language': feed_lang,
                        'summary': summary,
                        'published_at': published,
                    })
        except Exception as e:
            logger.warning(f"Feed error for {feed_info.get('name', region)}: {e}")
    
    # 2. Google News RSS with region-specific query (local language)
    query = source_config.get("google_news_query", f"{region} EV charging")
    google_articles = _get_google_news_rss(query, region_lang)
    for a in google_articles:
        a['region'] = region
        a['source'] = f"Google News ({region_lang})"
    articles.extend(google_articles)
    
    # 3. Fallback: English Google News query for broader coverage
    en_query = f"{region} EV charging electric vehicle"
    en_articles = _get_google_news_rss(en_query, "en")
    for a in en_articles:
        a['region'] = region
        a['source'] = f"Google News"
    articles.extend(en_articles)
    
    return articles


def collect_all_regions() -> dict[str, list[dict]]:
    """Collect articles from all regions."""
    results = {}
    for region in SOURCES:
        logger.info(f"Collecting from {region}...")
        try:
            articles = collect_from_rss(region)
            results[region] = articles
            logger.info(f"  -> {len(articles)} articles from {region}")
        except Exception as e:
            logger.error(f"Failed to collect {region}: {e}")
            results[region] = []
    return results

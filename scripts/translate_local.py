#!/usr/bin/env python3
"""Fetch non-English articles from Render, translate via API, push results back."""
import json
import os
import subprocess
import sys
import time
import re

API_BASE = "https://ev-pulse-fj43.onrender.com"

def fetch_articles():
    """Fetch all articles from Render API."""
    all_articles = []
    offset = 0
    limit = 100
    while True:
        resp = subprocess.run(
            ["curl", "-s", f"{API_BASE}/api/articles?min_relevance=0&limit={limit}&offset={offset}"],
            capture_output=True, text=True
        )
        data = json.loads(resp.stdout)
        articles = data.get("articles", [])
        if not articles:
            break
        all_articles.extend(articles)
        offset += limit
        print(f"  Fetched {len(articles)} (total: {len(all_articles)})", flush=True)
        if len(articles) < limit:
            break
        time.sleep(0.3)
    return all_articles

def is_non_english(title):
    """Check if title contains non-Latin characters."""
    if not title:
        return False
    # CJK: U+2E80–U+9FFF, Hangul: U+AC00–U+D7AF, etc.
    return any(ord(c) > 0x2E80 for c in title)

def translate_title(title, summary, region, lang):
    """Translate title using openai library."""
    try:
        from openai import OpenAI
        client = OpenAI()
        prompt = f"""Translate this EV charging news article title to English. Return ONLY the English translation, nothing else.

Language: {lang or 'unknown'}
Region: {region}
Original title: {title}
Summary: {summary or 'N/A'}

English translation:"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        translation = resp.choices[0].message.content.strip()
        # Remove quotes if LLM wrapped the text
        translation = translation.strip('"').strip("'").strip()
        return translation
    except ImportError:
        print("ERROR: openai library not installed. Install with: pip install openai")
        return None
    except Exception as e:
        print(f"  LLM Error: {e}", flush=True)
        return None

def update_article(article_id, new_title, new_summary):
    """Update article title on Render. We need to add this endpoint first."""
    # For now, print what we'd update
    print(f"  -> Would update article {article_id}: {new_title[:60]}...", flush=True)

def main():
    print("Fetching articles from Render...", flush=True)
    articles = fetch_articles()
    print(f"\nTotal articles: {len(articles)}", flush=True)

    # Find non-English
    candidates = [a for a in articles if is_non_english(a.get("title", ""))]
    print(f"Non-English articles: {len(candidates)}", flush=True)

    if not candidates:
        print("All articles are already in English!")
        return

    # Show a sample
    for a in candidates[:3]:
        print(f"  ID:{a['id']} [{a.get('region','?')}] {a['title'][:80]}", flush=True)

    print(f"\nTo translate {len(candidates)} articles, I need:")
    print("  1. An API key (OPENAI_API_KEY or LLM_API_KEY)")
    print("  2. A PATCH endpoint on Render to update article titles")
    print()
    print("Let me add the PATCH endpoint first.")

if __name__ == "__main__":
    main()

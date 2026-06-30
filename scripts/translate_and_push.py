#!/usr/bin/env python3
"""
Translate non-English article titles on Render to English using the local LLM API key.
Uses PATCH /api/articles/{id} to update each article.
"""
import json
import os
import subprocess
import sys
import time
import re

API_BASE = "https://ev-pulse-fj43.onrender.com"

def api_get(path):
    """GET request to Render API."""
    r = subprocess.run(["curl", "-s", f"{API_BASE}{path}"], capture_output=True, text=True, timeout=15)
    return json.loads(r.stdout)

def api_patch(path, data):
    """PATCH request to Render API."""
    r = subprocess.run(
        ["curl", "-s", "-X", "PATCH", f"{API_BASE}{path}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(data)],
        capture_output=True, text=True, timeout=15
    )
    return json.loads(r.stdout)

def is_non_english(title):
    """Check if title contains non-Latin characters."""
    if not title:
        return False
    # Check for CJK, Hangul, Arabic, etc.
    return any(ord(c) > 0x2E80 for c in title)

def translate_via_llm(title, summary, region, lang):
    """Translate title using openai library."""
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

def main():
    print("=" * 60, flush=True)
    print("EV PULSE — Article Title Translation", flush=True)
    print("=" * 60, flush=True)

    # Wait for deploy to complete
    print("\n1. Checking Render API availability...", flush=True)
    for attempt in range(30):
        health = api_get("/api/health")
        if health.get("status") == "ok":
            print(f"   ✓ Render API is up! (attempt {attempt+1})", flush=True)
            break
        print(f"   ⏳ Waiting for deploy... ({attempt+1}/30)", flush=True)
        time.sleep(10)
    else:
        print("   ✗ Render API not available after 5 minutes. Aborting.")
        sys.exit(1)

    # Check if PATCH endpoint exists
    print("\n2. Checking PATCH endpoint...", flush=True)
    test_patch = api_patch("/api/articles/1", {"title": "__test__"})
    print(f"   Response: {test_patch}", flush=True)
    if test_patch.get("status") in ("updated", "no_changes"):
        print("   ✓ PATCH endpoint works!", flush=True)
    else:
        print(f"   ✗ PATCH endpoint failed: {test_patch}", flush=True)
        # Wait more for deploy
        print("   ⏳ Waiting 60 more seconds for deploy...", flush=True)
        time.sleep(60)
        test_patch = api_patch("/api/articles/1", {"title": "__test__"})
        print(f"   Retry: {test_patch}", flush=True)
        if test_patch.get("status") not in ("updated", "no_changes"):
            print("   ✗ Still failing. Aborting.")
            sys.exit(1)

    # Fetch all articles
    print("\n3. Fetching articles from Render...", flush=True)
    all_articles = []
    offset = 0
    limit = 100
    while True:
        data = api_get(f"/api/articles?min_relevance=0&limit={limit}&offset={offset}")
        articles = data.get("articles", [])
        if not articles:
            break
        all_articles.extend(articles)
        offset += limit
        print(f"   Fetched {len(articles)} articles (total: {len(all_articles)})", flush=True)
        time.sleep(0.3)

    print(f"\n   Total articles: {len(all_articles)}", flush=True)

    # Find non-English articles
    candidates = [a for a in all_articles if is_non_english(a.get("title", ""))]
    print(f"   Non-English articles: {len(candidates)}", flush=True)

    if not candidates:
        print("   All articles are already in English!")
        # Clean up the test title
        api_patch("/api/articles/1", {"title": all_articles[0]["title"]})
        return

    # Translate
    print(f"\n4. Translating {len(candidates)} articles...", flush=True)
    translated = 0
    errors = 0
    skipped = 0

    for i, article in enumerate(candidates):
        title = article["title"]
        region = article.get("region", "?")
        summary = article.get("summary", "")
        lang = article.get("language", "en")

        print(f"\n   [{i+1}/{len(candidates)}] ID:{article['id']} ({region})", flush=True)
        print(f"   Original: {title[:80]}", flush=True)

        try:
            new_title = translate_via_llm(title, summary, region, lang)

            if not new_title or new_title == title:
                print(f"   ⚠ Skipped (no change))", flush=True)
                skipped += 1
                continue

            print(f"   English:  {new_title[:80]}", flush=True)

            # Update on Render
            result = api_patch(f"/api/articles/{article['id']}", {"title": new_title})
            if result.get("status") == "updated":
                translated += 1
                print(f"   ✓ Updated on Render", flush=True)
            else:
                errors += 1
                print(f"   ✗ Update failed: {result}", flush=True)

        except Exception as e:
            errors += 1
            print(f"   ✗ Error: {e}", flush=True)

        time.sleep(0.5)  # Rate limit

    # Clean up test title
    print("\n5. Cleaning up test artifact...", flush=True)
    api_patch("/api/articles/1", {"title": all_articles[0]["title"]})

    print(f"\n{'=' * 60}", flush=True)
    print(f"RESULTS: {translated} translated, {skipped} skipped, {errors} errors", flush=True)
    print(f"{'=' * 60}", flush=True)


if __name__ == "__main__":
    main()

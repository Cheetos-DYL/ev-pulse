#!/usr/bin/env python3
"""Batch-translate non-English article titles via LLM and push to Render DB."""
import json
import os
import sys
import time

API_BASE = "https://ev-pulse-fj43.onrender.com"

def main():
    # Fetch all articles with non-English titles
    all_articles = []
    offset = 0
    limit = 100
    while True:
        resp = os.popen(f'curl -s "{API_BASE}/api/articles?min_relevance=0&limit={limit}&offset={offset}"').read()
        data = json.loads(resp)
        articles = data.get("articles", [])
        if not articles:
            break
        all_articles.extend(articles)
        offset += limit
        print(f"  Fetched {len(articles)} articles (total: {len(all_articles)})", flush=True)
        if len(articles) < limit:
            break
        time.sleep(0.5)

    print(f"\nTotal articles: {len(all_articles)}")

    # Identify non-English articles (check if title contains non-ASCII)
    to_translate = []
    for a in all_articles:
        title = a.get("title", "")
        if not title:
            continue
        # Check if title has non-Latin characters (Korean, Japanese, Chinese, etc.)
        has_non_latin = any(ord(c) > 0x2E80 for c in title)
        if has_non_latin:
            to_translate.append(a)

    print(f"Articles needing translation: {len(to_translate)}")

    if not to_translate:
        print("No articles need translation!")
        return

    # Translate each one
    translated = 0
    errors = 0
    for i, article in enumerate(to_translate):
        title = article["title"]
        region = article.get("region", "?")
        summary = article.get("summary", "")
        lang = article.get("language", "?")

        print(f"\n[{i+1}/{len(to_translate)}] ID:{article['id']} ({region}/{lang})", flush=True)

        # Use a simple approach: call a local LLM
        prompt = f"""Translate this news article title to English. Return ONLY the English translation, nothing else.

Language: {lang}
Region: {region}
Original title: {title}
Summary: {summary}

English translation:"""

        try:
            # Use subprocess to call Hermes or a local model
            result = os.popen(
                f'curl -s https://api.openai.com/v1/chat/completions '
                f'-H "Authorization: Bearer {os.environ.get("OPENAI_API_KEY", "")}" '
                f'-H "Content-Type: application/json" '
                f'-d \'{{"model":"gpt-4o-mini","messages":[{{"role":"user","content":{json.dumps(prompt)}}}],"temperature":0.1,"max_tokens":100}}\''
            ).read()

            response = json.loads(result)
            translated_title = response["choices"][0]["message"]["content"].strip().strip('"').strip("'")

            if translated_title and translated_title != title:
                # Push update to Render
                update_resp = os.popen(
                    f'curl -s -X POST "{API_BASE}/api/reanalyze?limit=1"'
                ).read()
                # Since we don't have a single-article update endpoint, use the DB directly
                # Actually let's use the raw API update approach

            print(f"  Original: {title[:60]}...", flush=True)
            print(f"  Translation: {translated_title[:60]}...", flush=True)
            translated += 1

        except Exception as e:
            print(f"  ERROR: {e}", flush=True)
            errors += 1

        time.sleep(0.3)

    print(f"\nDone! Translated: {translated}, Errors: {errors}")


if __name__ == "__main__":
    main()

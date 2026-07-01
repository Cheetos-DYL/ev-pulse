# INTENT — EV Pulse

> status: clarified

## Why

**Who:** Me (OEM, Overseas EV Charging Services) and our department team members. Some key insights are occasionally forwarded to external teams on an ad-hoc basis.

**Problem:** EV charging service trends in each emerging market are changing fast, and it's not easy to keep up from the office. Individually tracking local news in different languages is impossible during work hours.

**Solution:** A tool that handles everything in one go — auto-scraping local news → English translation/analysis → archiving → periodic reports delivered to Telegram.

**Success metric:** The tool is working if the team regularly reads the weekly digest and monthly report instead of manually searching for market updates.

## What

- [x] **9 emerging markets coverage** (weighted by business relevance) — Korea, Japan, Taiwan, SE Asia, Australia, UAE/Middle East, Africa, Brazil, Mexico. Coverage depth adjusts per market. New markets added at my discretion.
- [x] **Auto collection/translation/classification from local languages to English** — DeepSeek API for title/summary translation, category classification, relevance scoring
- [x] **Web dashboard** — Country-by-country latest news, trends, stats, searchable article archive, and interactive charts. **Search must find any article from the last 6 months within 30 seconds.** Archive indexed by market, category, date, and keyword.
- [x] **Monthly report** — Deep analysis on the 1st, delivered to Telegram. Executive summary first, then per-market deep dives. Cross-market trends included. Period-over-period comparisons.
- [x] **Weekly digest** — Light update every Tuesday morning. TL;DR first, then per-market bullets in a threaded Telegram message.

---

### Weekly digest — Telegram format

```
📰 EV Pulse — Weekly Digest [Date]

🔥 TOP STORIES
[3 cross-market highlights — "why it matters" first]

───

🇰🇷 Korea
• [Why it matters → Headline | link]
• ...
───
🇯🇵 Japan
• ...
```

**Format rules:**
- **"Why it matters" comes first** in each bullet — the headline is secondary context
- TL;DR section with exactly 3 top cross-market stories
- Per-market sections in reply thread under main message
- Flag emojis for instant visual recognition

### Monthly report — Telegram format

```
📊 EV Pulse — Monthly Report [Month/Year]

🔥 EXECUTIVE SUMMARY
[Top 3 developments across all markets this month]

🌐 CROSS-MARKET TRENDS
[Patterns visible across multiple markets]

───

🇰🇷 Korea
[2–3 paragraph summary vs prior month]
Key stats: ...
[links]

───

🇯🇵 Japan
...
```

### Article classification & relevance scoring

**Categories (primary assignment rule):**
Each article gets ONE primary category. If multiple apply, priority: Government policy > M&A/Partnership > Charger Install > Charging Standards > Grid/Pricing > EV Sales/Stats.

**Relevance score (0–100):**
- **Keyword match (0–40):** Explicit mention of target terms (charging, EV, subsidy, station name, operator name)
- **Market impact (0–30):** Deal size, number of chargers, government budget involved — bigger = higher
- **Recency (0–20):** Full score within 7 days, decays to 0 after 30 days
- **Source authority (0–10):** Official govt/utility > local news > blog/social

Articles below configurable threshold excluded from digest/report but stored in archive.

**Translation quality:**
- DeepSeek handles title + summary translation — best-effort, no automated verification
- Low-confidence translations flagged in archive for optional human review

## Operations & Reliability

**Scheduling chain:**
1. **Collection cron** runs ~6h before delivery to gather and process articles. Buffer absorbs cold start delays.
2. **Delivery cron** runs at scheduled time using pre-collected data.
3. If collection fails, that market is skipped. Error noted in banner.

**Failure modes & handling:**
| Failure | Behavior |
|---------|----------|
| RSS feed down | Skip source, collect rest |
| DeepSeek API down | Fallback to keyword scoring + raw translation |
| Render cold start | Collections buffered; seed_data.json recovery on DB loss |
| Telegram delivery fail | Retry once after 5 min |
| All sources for a market down | Market shows as "no updates this period" |
| Link rot | Links live at time of reporting |

**Monitoring:** Heartbeat check (articles collected in last 48h). Delivery failures logged.

**Source confidence:**
- Each market's source list tagged: **stable** (reliable, >3 months) or **experimental** (new/temporary)
- Experimental sources flagged in archive. Markets with only experimental sources carry less weight.

## User flow

1. **Tuesday AM** → Weekly digest arrives. 10s scan of TL;DR → tap into markets of interest
2. **1st of month** → Monthly report arrives. Executive summary → drill into relevant markets
3. **As needed** → Web dashboard for archive search, charts, deep dives

## Not

- **Not for:** General public — internal team tool
- **No news without links:** Every item must include original source link
- **No real-time alerts:** Batch delivery (weekly/monthly) is sufficient
- **Out of scope:** New car launches, battery materials/mining, autonomous driving, developed markets (US/EU/China)
- **Tech constraint:** Render free tier (cold start OK, SQLite, no persistent DB)
- **No social media crawling, no 100% factual accuracy guarantee**
- **No link archive:** Links may rot over time
- **No automated translation verification:** Best-effort only

## Learnings

- [2025] OpenAI GPT → DeepSeek API. Quality equivalent, cost 1/5
- [2025] Render SQLite ephemeral → seed_data.json auto-recovery pattern
- [2025] Google News RSS unstable → Local publisher RSS as main source
- [2026-04] Removed openai library, urllib direct → Render crash resolved
- [2026-06] 9 regions stable for 6 months. Monthly report working.
- [2026-06] First INTENT.md written
- [2026-07] Weekly digest added. Telegram delivery (ESOS Agent group). Threaded format with TL;DR + "why it matters first". Cross-market trends & executive summary in monthly reports. Relevance scoring criteria defined. Source confidence tracking. Operations & reliability section.

**English only:** All reports, summaries, UI are 100% English. Local articles translated to English before display.

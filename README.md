# EV Pulse ⚡

**EV Charging Intelligence for Emerging Markets**

Monitoring EV charging services, market trends, and policy changes across 13 emerging markets.

## Target Regions

- 🇰🇷 Korea
- 🇦🇪 UAE / Middle East
- 🌏 Southeast Asia
- 🇯🇵 Japan
- 🇦🇺 Australia
- 🇹🇼 Taiwan
- 🌍 Africa / South Africa
- 🇧🇷 Brazil
- 🇲🇽 Mexico / Central America

## Tech Stack

- **Backend:** Python (FastAPI) + SQLite
- **Frontend:** React (Vite + TypeScript)
- **LLM:** OpenAI API (article filtering + report generation)
- **Deployment:** Render

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env  # Add your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # Runs on port 5173 with proxy to backend
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/articles` | List articles (filter by region, category, relevance) |
| GET | `/api/stats` | Dashboard statistics |
| POST | `/api/collect` | Collect articles from all regions |
| POST | `/api/collect/{region}` | Collect from a specific region |
| GET | `/api/reports` | List monthly reports |
| POST | `/api/reports/generate` | Generate a monthly report |

## Usage

1. **Collect articles** → POST `/api/collect` (or use Settings page)
2. **Browse dashboard** → View stats and filter articles
3. **Generate report** → POST `/api/reports/generate` (or use Reports page)

## Project Structure

```
ev-pulse/
├── backend/
│   ├── app/
│   │   ├── main.py      # FastAPI application
│   │   ├── db.py        # SQLite database
│   │   ├── scraper.py   # RSS feed collection
│   │   ├── analyzer.py  # LLM-powered filtering
│   │   ├── reporter.py  # Monthly report generation
│   │   └── sources.py   # RSS feeds and config
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx      # Dashboard, Articles, Reports pages
│   │   ├── api.ts       # API client
│   │   └── index.css    # Dark theme styles
│   └── package.json
├── data/                # SQLite database (auto-created)
├── render.yaml          # Render deployment config
└── README.md
```

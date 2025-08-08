Stocky.AI Backend - Pro scaffold

What is included:
- FastAPI app with /market, /trade, /auth, /ai routers
- Polygon/Finnhub provider hooks (use POLYGON_API_KEY or FINNHUB_API_KEY env vars)
- Redis caching support (set REDIS_URL)
- Indicators computed with pandas (SMA/EMA/RSI/MACD/Bollinger)
- Simple JWT auth for demo users
- OpenAI proxy (set OPENAI_API_KEY) or falls back to dummy

Env variables (.env):
POLYGON_API_KEY=
FINNHUB_API_KEY=
REDIS_URL=
JWT_SECRET=
OPENAI_API_KEY=
CORS_ORIGINS=*

Run locally:
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

Deploy to Render or any container service. Use $PORT in start command.

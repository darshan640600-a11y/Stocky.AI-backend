
import os
import datetime
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .routes import market, trade, auth, ai
from .utils import init_redis

app = FastAPI(title="Stocky.AI Backend (Pro)", version="1.0.0")

# CORS - restrict in production via CORS_ORIGINS env var (comma separated)
origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",")] if origins_env != "*" else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Initialize optional Redis (for caching)
REDIS = init_redis(os.getenv("REDIS_URL"))

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(trade.router, prefix="/trade", tags=["trade"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])

# Health & ping endpoints (supports HEAD)
@app.get("/")
@app.head("/")
def health():
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat()}

@app.get("/ping")
def ping():
    return {"status":"ok"}

# Global exception handler (simple)
@app.exception_handler(Exception)
async def generic_exception(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

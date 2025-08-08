
from fastapi import APIRouter, Query, HTTPException, Depends
from ..utils import get_candles, compute_indicators
from ..main import REDIS

router = APIRouter()

@router.get("/candles")
def candles(symbol: str = Query(..., min_length=1), days: int = 30, resolution: str = "1d", include_indicators: bool = True):
    try:
        data = get_candles(symbol, period_days=days, resolution=resolution, redis_client=REDIS)
        candles = data.get("candles", [])
        indicators = compute_indicators(candles) if include_indicators else {}
        return {"symbol": symbol, "candles": candles, "indicators": indicators}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

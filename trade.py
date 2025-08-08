
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid, time

router = APIRouter()
_positions = {}

class Order(BaseModel):
    user: str
    symbol: str
    side: str
    qty: float

@router.post("/simulate")
def simulate(order: Order):
    trade = {"id": str(uuid.uuid4()), "user": order.user, "symbol": order.symbol, "side": order.side, "qty": order.qty, "price": 100.0, "time": int(time.time())}
    _positions.setdefault(order.user, []).append(trade)
    return {"ok": True, "trade": trade}

@router.get("/positions/{user}")
def positions(user: str):
    return {"user": user, "positions": _positions.get(user, [])}

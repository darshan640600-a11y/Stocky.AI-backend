
import os
import time
import json
import requests
import pandas as pd
import numpy as np

def init_redis(url):
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url)
    except Exception as e:
        print("Redis init failed:", e)
        return None

# -- Market provider: Polygon (preferred) or Finnhub fallback --
def fetch_ohlc_polygon(symbol, from_ts, to_ts, timespan='day', api_key=None):
    # Polygon historic aggregates endpoint (daily): /v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from}/{to}
    if not api_key:
        return {"error":"no_api_key"}
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/{timespan}/{from_ts}/{to_ts}?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
    r = requests.get(url, timeout=15)
    if r.status_code!=200:
        return {"error":"provider_error","status":r.status_code,"text":r.text}
    j = r.json()
    results = j.get('results', [])
    candles = []
    for item in results:
        candles.append({
            "t": int(item['t']//1000), # seconds
            "o": item['o'],
            "h": item['h'],
            "l": item['l'],
            "c": item['c'],
            "v": item.get('v', 0)
        })
    return {"candles": candles}

def fetch_ohlc_finnhub(symbol, from_ts, to_ts, resolution='D', api_key=None):
    if not api_key:
        return {"error":"no_api_key"}
    url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution={resolution}&from={from_ts}&to={to_ts}&token={api_key}"
    r = requests.get(url, timeout=12)
    if r.status_code!=200:
        return {"error":"provider_error","status":r.status_code,"text":r.text}
    j = r.json()
    if j.get('s')!='ok':
        return {"error":"no_data"}
    candles = []
    for i in range(len(j['t'])):
        candles.append({
            "t": int(j['t'][i]),
            "o": j['o'][i],
            "h": j['h'][i],
            "l": j['l'][i],
            "c": j['c'][i],
            "v": j.get('v', [None]*len(j['t']))[i] if 'v' in j else None
        })
    return {"candles": candles}

# Compute indicators: SMA, EMA, RSI, MACD, Bollinger Bands
def compute_indicators(candles):
    if not candles:
        return {}
    df = pd.DataFrame(candles)
    # ensure time sorted ascending
    df = df.sort_values('t').reset_index(drop=True)
    close = df['c'].astype(float)

    def sma(series, period):
        return series.rolling(window=period).mean().tolist()

    def ema(series, period):
        return series.ewm(span=period, adjust=False).mean().tolist()

    def rsi(series, period=14):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1*delta.clip(upper=0)
        ma_up = up.ewm(com=period-1, adjust=False).mean()
        ma_down = down.ewm(com=period-1, adjust=False).mean()
        rs = ma_up / ma_down
        return (100 - (100/(1+rs))).tolist()

    # MACD
    ema12 = pd.Series(close).ewm(span=12, adjust=False).mean()
    ema26 = pd.Series(close).ewm(span=26, adjust=False).mean()
    macd_line = (ema12 - ema26)
    signal = macd_line.ewm(span=9, adjust=False).mean()

    bb_middle = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    bb_upper = bb_middle + (bb_std * 2)
    bb_lower = bb_middle - (bb_std * 2)

    indicators = {
        "sma_20": sma(close,20),
        "ema_20": ema(close,20),
        "rsi_14": rsi(close,14),
        "macd_line": macd_line.tolist(),
        "macd_signal": signal.tolist(),
        "bb_upper": bb_upper.tolist(),
        "bb_lower": bb_lower.tolist(),
        "bb_middle": bb_middle.tolist()
    }
    return indicators

# Helper to try providers and caching
def get_candles(symbol, period_days=30, resolution='1d', redis_client=None):
    now = int(time.time())
    to_ts = now
    from_ts = now - period_days*24*60*60
    cache_key = f"candles:{symbol}:{period_days}:{resolution}"
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return {"candles": json.loads(cached)}
        except Exception as e:
            print("Redis get error:", e)

    # Try Polygon first
    polygon_key = os.getenv('POLYGON_API_KEY')
    res = {}
    if polygon_key:
        res = fetch_ohlc_polygon(symbol, from_ts*1000, to_ts*1000, timespan='day', api_key=polygon_key)
    # If polygon failed, try finnhub
    if res.get('error'):
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_key:
            res = fetch_ohlc_finnhub(symbol, from_ts, to_ts, resolution='D', api_key=finnhub_key)
    # If still error, return mock
    if res.get('error'):
        # generate mock candles
        candles = []
        for i in range(period_days):
            ts = (from_ts + i*24*60*60)
            base = 100 + (i%10) + (i*0.1)
            candles.append({"t": ts, "o": base, "h": base+1, "l": base-1, "c": base+0.2, "v": 1000})
        res = {"candles": candles}

    # Cache result
    if redis_client:
        try:
            redis_client.set(cache_key, json.dumps(res['candles']), ex=60*60)  # cache 1 hour
        except Exception as e:
            print("Redis set error:", e)

    return res

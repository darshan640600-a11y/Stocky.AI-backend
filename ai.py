
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os, requests

router = APIRouter()

class ChatIn(BaseModel):
    message: str

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

@router.post("/chat")
def chat(payload: ChatIn):
    if not OPENAI_KEY:
        # return dummy response
        return {"reply": f"Echo: {payload.message}"}
    # proxy to OpenAI (example): ensure you implement usage limits & billing checks
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type":"application/json"}
    body = {"model":"gpt-4o-mini","messages":[{"role":"user","content":payload.message}],"max_tokens":250}
    r = requests.post(url, headers=headers, json=body, timeout=15)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="OpenAI error")
    return r.json()

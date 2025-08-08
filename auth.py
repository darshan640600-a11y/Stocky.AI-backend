
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.hash import bcrypt
import jwt, os, time

router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")
JWT_ALGO = "HS256"
_users = {}

class Signup(BaseModel):
    username: str
    password: str

class Login(BaseModel):
    username: str
    password: str

@router.post("/signup")
def signup(u: Signup):
    if u.username in _users:
        raise HTTPException(status_code=400, detail="exists")
    _users[u.username] = {"pw": bcrypt.hash(u.password), "created": int(time.time())}
    return {"ok": True}

@router.post("/login")
def login(u: Login):
    user = _users.get(u.username)
    if not user or not bcrypt.verify(u.password, user["pw"]):
        raise HTTPException(status_code=401, detail="invalid")
    token = jwt.encode({"sub": u.username, "iat": int(time.time())}, JWT_SECRET, algorithm=JWT_ALGO)
    return {"access_token": token}

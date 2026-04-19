import datetime
from typing import Dict
import jwt
from fastapi import FastAPI, Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
import secrets

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

fake_users_db = {}

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def get_user(username: str) -> UserInDB | None:
    user_dict = fake_users_db.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> UserInDB | None:
    user = get_user(username)
    if not user:
        return None
    if not secrets.compare_digest(username, user.username):
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user

def create_jwt_token(data: Dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_from_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def register(request: Request, user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=409, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)
    user_in_db = UserInDB(username=user.username, hashed_password=hashed_password)
    fake_users_db[user.username] = user_in_db.model_dump()

    return {"message": f"User '{user.username}' created"}

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user_in: User):
    user_dict = fake_users_db.get(user_in.username)

    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = UserInDB(**user_dict)

    is_correct_username = secrets.compare_digest(user_in.username, user.username)
    is_correct_password = pwd_context.verify(user_in.password, user.hashed_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    token = create_jwt_token({"sub": user_in.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected_resource")
def protected_resource(username: str = Depends(get_user_from_token)):
    return {"message": "Access granted", "user": username}
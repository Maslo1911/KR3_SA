from fastapi import FastAPI, Depends, status, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
import secrets

class Settings(BaseSettings):
    MODE: str = "DEV"
    DOCS_USER: str
    DOCS_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None if settings.MODE == "PROD" else "/openapi.json"
)
security = HTTPBasic()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

fake_users_db = {}

def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.DOCS_USER)
    correct_password = secrets.compare_digest(credentials.password, settings.DOCS_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    user_dict = fake_users_db.get(credentials.username)

    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = UserInDB(**user_dict)

    is_correct_username = secrets.compare_digest(credentials.username, user.username)
    is_correct_password = pwd_context.verify(credentials.password, user.hashed_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user

@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi(request: Request):
    if settings.MODE == "PROD":
        raise HTTPException(status_code=404)
    # В DEV — проверяем credentials вручную из заголовка
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )
    import base64
    try:
        decoded = base64.b64decode(auth[6:]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not (secrets.compare_digest(username, settings.DOCS_USER) and
            secrets.compare_digest(password, settings.DOCS_PASSWORD)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


@app.get(
    "/docs",
    include_in_schema=False,
    dependencies=[Depends(verify_docs_credentials)] if settings.MODE == "DEV" else [],
)
async def custom_docs():
    if settings.MODE == "PROD":
        raise HTTPException(status_code=404)
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    raise HTTPException(status_code=404)

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)

    user_in_db = UserInDB(username=user.username, hashed_password=hashed_password)
    fake_users_db[user.username] = user_in_db.model_dump()

    return {"message": f"User {user.username} registered successfully"}

@app.get("/login")
def login(user: UserInDB = Depends(auth_user)):
    return {"message": f"Welcome, {user.username}!"}
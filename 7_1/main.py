from fastapi import FastAPI, Depends, HTTPException, status
from security import create_jwt_token
from models import UserLogin, User, Permissions
from db import USERS_DATA
from dependencies import get_current_user
from rbac import PermissionChecker

app = FastAPI(title="RBAC Demo")

@app.post("/login")
async def login(user_in: UserLogin):
    for user in USERS_DATA:
        if user["username"] == user_in.username and user["password"] == user_in.password:
            token = create_jwt_token({"sub": user_in.username})
            return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учётные данные",
    )

@app.get("/public")
@PermissionChecker([Permissions.READ_PUBLIC])
async def public_info(current_user: User = Depends(get_current_user)):
    return {"message": f"Привет, {current_user.username}! Это публичная страница."}

@app.get("/protected_resource")
@PermissionChecker([Permissions.READ_RESOURCE])
async def protected_resource(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Доступ разрешён, {current_user.username}!",
        "your_roles": current_user.roles,
    }

@app.get("/admin/users")
@PermissionChecker([Permissions.READ_USERS])
async def admin_read_users(current_user: User = Depends(get_current_user)):
    return {"message": f"{current_user.username}: список пользователей получен."}


@app.post("/admin/users")
@PermissionChecker([Permissions.WRITE_USERS])
async def admin_write_users(current_user: User = Depends(get_current_user)):
    return {"message": f"{current_user.username}: пользователь создан/обновлён."}


@app.delete("/admin/users/{user_id}")
@PermissionChecker([Permissions.DELETE_USERS])
async def admin_delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    return {"message": f"{current_user.username}: пользователь {user_id} удалён."}


@app.get("/resource")
@PermissionChecker([Permissions.READ_RESOURCE])
async def read_resource(current_user: User = Depends(get_current_user)):
    return {"message": f"{current_user.username}: ресурс прочитан."}


@app.post("/resource")
@PermissionChecker([Permissions.WRITE_RESOURCE])
async def write_resource(current_user: User = Depends(get_current_user)):
    return {"message": f"{current_user.username}: ресурс обновлён."}

@app.get("/about_me")
async def about_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "full_name": current_user.full_name,
        "roles": current_user.roles,
        "permissions": sorted(current_user.permissions),
    }
from fastapi import Depends, HTTPException, status
from security import get_user_from_token
from db import get_user
from models import User


def get_current_user(current_username: str = Depends(get_user_from_token)) -> User:
    user = get_user(current_username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь отключён")
    return user
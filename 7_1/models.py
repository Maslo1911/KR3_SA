from pydantic import BaseModel, EmailStr, Field, model_validator
from enum import Enum


class Permissions(str, Enum):
    # CRUD над пользователями
    READ_USERS   = "read:users"
    WRITE_USERS  = "write:users"
    DELETE_USERS = "delete:users"
    # Ресурсы
    READ_RESOURCE  = "read:resource"
    WRITE_RESOURCE = "write:resource"
    # Только для гостя
    READ_PUBLIC = "read:public"


class Role(BaseModel):
    name: str
    permissions: list[str]


class User(BaseModel):
    username: str
    full_name: str | None = None
    email: EmailStr | None = None
    disabled: bool = False
    roles: list[str]
    permissions: set[str] = Field(default_factory=set)
    extra_permissions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_permissions(self):
        from db import ROLES_REGISTRY
        all_permissions: set[str] = set()
        for role_name in self.roles:
            if role_name in ROLES_REGISTRY:
                all_permissions.update(ROLES_REGISTRY[role_name].permissions)
        all_permissions.update(self.extra_permissions)
        self.permissions = all_permissions
        return self


class UserLogin(BaseModel):
    username: str
    password: str
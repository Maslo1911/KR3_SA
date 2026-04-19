from models import User, Role, Permissions

ROLES_REGISTRY: dict[str, Role] = {
    "admin": Role(
        name="admin",
        permissions=[
            Permissions.READ_USERS,
            Permissions.WRITE_USERS,
            Permissions.DELETE_USERS,
            Permissions.READ_RESOURCE,
            Permissions.WRITE_RESOURCE,
            Permissions.READ_PUBLIC,
        ],
    ),
    "user": Role(
        name="user",
        permissions=[
            Permissions.READ_USERS,
            Permissions.READ_RESOURCE,
            Permissions.WRITE_RESOURCE,
            Permissions.READ_PUBLIC,
        ],
    ),
    "guest": Role(
        name="guest",
        permissions=[
            Permissions.READ_PUBLIC,
        ],
    ),
}

USERS_DATA = [
    {
        "username": "admin",
        "password": "adminpass",
        "roles": ["admin"],
        "full_name": "Admin User",
        "email": "admin@example.com",
        "disabled": False,
    },
    {
        "username": "alice",
        "password": "userpass",
        "roles": ["user"],
        "full_name": "Alice",
        "email": "alice@example.com",
        "disabled": False,
    },
    {
        "username": "guest",
        "password": "guestpass",
        "roles": ["guest"],
        "full_name": "Guest User",
        "email": "guest@example.com",
        "disabled": False,
    },
]

def get_user(username: str) -> User | None:
    for user_data in USERS_DATA:
        if user_data["username"] == username:
            return User(**{k: v for k, v in user_data.items() if k != "password"})
    return None
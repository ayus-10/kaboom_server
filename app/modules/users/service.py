from app.modules.users.schemas import User

class UsersService:
    def get_all_users(self) -> list[User]:
        return [
            User(id=1, email="alice@example.com"),
            User(id=2, email="bob@example.com"),
        ]

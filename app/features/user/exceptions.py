class UserServiceError(Exception):
    pass


class UserNotFoundError(UserServiceError):
    pass

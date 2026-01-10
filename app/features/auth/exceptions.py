class OAuthExchangeError(Exception):
    pass


class TokenVerificationError(Exception):
    pass


class AuthServiceError(Exception):
    pass


class InvalidRefreshTokenError(AuthServiceError):
    pass

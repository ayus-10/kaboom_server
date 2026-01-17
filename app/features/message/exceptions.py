class MessageServiceError(Exception):
    pass

class MessageAuthorizationError(MessageServiceError):
    pass

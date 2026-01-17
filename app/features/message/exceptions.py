class MessageServiceError(Exception):
    pass

class MessageAuthorizationError(MessageServiceError): # suggest a bettername
    pass

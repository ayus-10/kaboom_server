class PendingConversationServiceError(Exception):
    pass

class InvalidVisitorIDError(PendingConversationServiceError):
    pass

class PendingConversationNotFoundError(PendingConversationServiceError):
    pass

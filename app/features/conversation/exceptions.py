class ConversationServiceError(Exception):
    pass

class PendingConversationNotFoundError(ConversationServiceError):
    pass

class ConversationNotFoundError(ConversationServiceError):
    pass

class ConversationAlreadyExistsError(ConversationServiceError):
    pass

class ConversationAuthorizationError(ConversationServiceError):
    pass

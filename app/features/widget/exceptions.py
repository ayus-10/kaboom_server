class WidgetServiceError(Exception):
    pass

class WidgetNotFoundError(WidgetServiceError):
    pass

class WidgetAccessDeniedError(WidgetServiceError):
    pass

class WidgetServiceError(Exception):
    pass

class WidgetNotFound(WidgetServiceError):
    pass

class WidgetAccessDenied(WidgetServiceError):
    pass

class ProjectServiceError(Exception):
    pass

class ProjectNotFound(ProjectServiceError):
    pass

class ProjectAccessDenied(ProjectServiceError):
    pass

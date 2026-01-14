class ProjectServiceError(Exception):
    pass

class ProjectNotFound(ProjectServiceError):
    pass

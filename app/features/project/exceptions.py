class ProjectServiceError(Exception):
    pass

class ProjectNotFoundError(ProjectServiceError):
    pass

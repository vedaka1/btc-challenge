class ApplicationError(Exception):
    pass


class ObjectAlreadyExistsError(ApplicationError):
    def __init__(self):
        super().__init__("Object already exists")


class ObjectNotFoundError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message)

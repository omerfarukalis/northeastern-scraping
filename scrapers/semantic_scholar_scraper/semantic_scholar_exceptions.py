class SemanticScholarException(Exception):
    """
    The base class for SemanticScholar exceptions
    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class BadQueryParametersException(SemanticScholarException):
    '''Bad query parameters'''
    pass


class ObjectNotFoundException(SemanticScholarException):
    """Object not found"""
    pass

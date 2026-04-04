class ArrowException(Exception):
    """
    Base exception class for all Arrow-related errors.

    Attributes:
        message (str): A description of the error.
        code (int): An optional HTTP-style status code (default: 500).
    """

    def __init__(self, message: str, code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class GeneralException(ArrowException):
    """
    Represents general application-level exceptions in Arrow.
    Typically used for unexpected or generic failures.
    """

    def __init__(self, message: str, code: int = 500) -> None:
        super().__init__(message, code)


class DataException(ArrowException):
    """
    Represents exceptions related to data processing or retrieval
    within Arrow. Use this when a data fetch, parse, or validation fails.
    """

    def __init__(self, message: str, code: int = 502) -> None:
        super().__init__(message, code)

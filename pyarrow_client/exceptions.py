from typing import Optional

_HTTP_STATUS_NAMES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


class ArrowException(Exception):
    """
    Base exception class for all Arrow-related errors.

    Attributes:
        message (str): A description of the error.
        code (int): An optional HTTP-style status code (default: 500).
        method (str | None): HTTP method of the failed request.
        url (str | None): URL of the failed request.
    """

    def __init__(
        self,
        message: str,
        code: int = 500,
        method: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.method = method
        self.url = url

    def __str__(self) -> str:
        status_name = _HTTP_STATUS_NAMES.get(self.code, "")
        status_text = f"{self.code} ({status_name})" if status_name else str(self.code)

        lines = [
            "",
            "╭─ Arrow API Error ────────────────────────────────────────",
            f"│ Status  : {status_text}",
            f"│ Message : {self.message}",
        ]
        if self.method and self.url:
            lines.append(f"│ Request : {self.method} {self.url}")
        lines.append("╰──────────────────────────────────────────────────────────")

        return "\n".join(lines)


class GeneralException(ArrowException):
    """
    Represents general application-level exceptions in Arrow.
    Typically used for unexpected or generic failures.
    """

    def __init__(
        self,
        message: str,
        code: int = 500,
        method: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        super().__init__(message, code, method, url)


class DataException(ArrowException):
    """
    Represents exceptions related to data processing or retrieval
    within Arrow. Use this when a data fetch, parse, or validation fails.
    """

    def __init__(
        self,
        message: str,
        code: int = 502,
        method: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        super().__init__(message, code, method, url)

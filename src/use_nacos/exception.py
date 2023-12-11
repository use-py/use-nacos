from enum import Enum
from typing import Optional

import httpx


class HTTPResponseError(Exception):
    """Exception for HTTP errors.

    Responses from the API use HTTP response codes that are used to indicate general
    classes of success and error.
    """

    code: str = "client_response_error"
    status: int
    headers: httpx.Headers
    body: str

    def __init__(self, response: httpx.Response, message: Optional[str] = None) -> None:
        if message is None:
            message = (
                f"Request to Nacos API failed: {response.text}"
            )
        super().__init__(message)
        self.status = response.status_code
        self.headers = response.headers
        self.body = response.text

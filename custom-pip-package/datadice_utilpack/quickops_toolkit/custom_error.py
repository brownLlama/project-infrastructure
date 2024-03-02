"""
In this file we are creating custom errors such that logging is improved.

Currently it contains:
- UpsertRequestError
- DeleteRequestError
- APIRequestError
- GetRequestError
"""


class UpsertRequestError(Exception):
    """
    Exception to be raised when an API Upsert request fails.

    Attributes:
        status_code (int): The HTTP status code returned by the failed request.
        content (str): The content of the HTTP response.
    """

    def __init__(self, status_code, content):
        """
        Initialize the UpsertRequestError with the provided status code and content.

        Args:
            status_code (int): The HTTP status code returned by the failed request.
            content (str): The content of the HTTP response.
        """
        super().__init__(
            f"Request failed with status {status_code}. Response: {content}"
        )
        self.status_code = status_code
        self.content = content


class DeleteRequestError(Exception):
    """
    Exception to be raised when an API Delete request fails.

    Attributes:
        status_code (int): The HTTP status code returned by the failed request.
        content (str): The content of the HTTP response.
    """

    def __init__(self, status_code, content):
        """
        Initialize the DeleteRequestError with the provided status code and content.

        Args:
            status_code (int): The HTTP status code returned by the failed request.
            content (str): The content of the HTTP response.
        """
        super().__init__(
            f"Request failed with status {status_code}. Response: {content}"
        )
        self.status_code = status_code
        self.content = content


class GetRequestError(Exception):
    """
    Exception to be raised when an API Get request fails.

    Attributes:
        status_code (int): The HTTP status code returned by the failed request.
        content (str): The content of the HTTP response.
    """

    def __init__(self, status_code, content):
        """
        Initialize the GetRequestError with the provided status code and content.

        Args:
            status_code (int): The HTTP status code returned by the failed request.
            content (str): The content of the HTTP response.
        """
        super().__init__(
            f"Request failed with status {status_code}. Response: {content}"
        )
        self.status_code = status_code
        self.content = content


class APIRequestError(Exception):
    """
    Exception to be raised when an API request fails.

    Attributes:
        status_code (int): The HTTP status code returned by the failed request.
        content (str): The content of the HTTP response.
    """

    def __init__(self, status_code, content):
        """
        Initialize the APIRequestError with the provided status code and content.

        Args:
            status_code (int): The HTTP status code returned by the failed request.
            content (str): The content of the HTTP response.
        """
        super().__init__(
            f"Request failed with status {status_code}. Response: {content}"
        )
        self.status_code = status_code
        self.content = content

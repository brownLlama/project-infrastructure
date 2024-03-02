"""
This module provides facilities for creating HTTP sessions with customized settings for GET and POST requests.

Example:
    factory = HTTPSessionFactory()
    get_http_session = factory.get_http_session()
    post_http_session = factory.post_http_session()

    response_get = get_http_session.get(url=url)
    response_post = post_http_session.post(url=url, data=data)
"""

from typing import Any, Dict, Tuple

import requests
from requests import PreparedRequest, Response, Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    HTTPAdapter with adjustable timeout, inheriting requests.adapters.HTTPAdapter.

    Attributes:
        DEFAULT_TIMEOUT (int): Default timeout value.
    """

    DEFAULT_TIMEOUT = 5

    def __init__(self, *args: Tuple[Any], **kwargs: Dict[str, Any]):
        """
        Initialize TimeoutHTTPAdapter with provided timeout or the default timeout.

        Args:
            *args (Tuple[Any]): Variable length argument list.
            **kwargs (Dict[str, Any]): Arbitrary keyword arguments.
        """
        self.timeout = kwargs.pop("timeout", self.DEFAULT_TIMEOUT)
        super().__init__(*args, **kwargs)

    def send(self, request: PreparedRequest, **kwargs: Dict[str, Any]) -> Response:
        """
        Override the send method of HTTPAdapter to include timeout in the request kwargs.

        Args:
            request (PreparedRequest): The HTTP request to send.
            **kwargs (Dict[str, Any]): Arbitrary keyword arguments.

        Returns:
            Response: The server's response to the request.
        """
        kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


class HTTPSessionFactory:
    """Factory for creating HTTP sessions with customized settings."""

    def __init__(self):
        """Initialize HTTPSessionFactory with GET and POST adapters with retry strategies."""
        self.get_adapter = TimeoutHTTPAdapter(
            timeout=(3, 60),
            max_retries=Retry(
                total=5,
                respect_retry_after_header=False,
                connect=5,
                read=5,
                backoff_factor=1.5,
                allowed_methods=False,
                status_forcelist=[429, 500, 502, 503, 504],
            ),
        )
        self.post_retry_strategy = Retry(
            total=5, backoff_factor=1, allowed_methods=frozenset(["GET", "POST"])
        )
        self.post_adapter = HTTPAdapter(max_retries=self.post_retry_strategy)

    def get_http_session(self) -> Session:
        """
        Create and return a new HTTP session for GET requests.

        Returns:
            Session: The newly created HTTP session.
        """
        return self._create_http_session(self.get_adapter)

    def post_http_session(self) -> Session:
        """
        Create and return a new HTTP session for POST requests.

        Returns:
            Session: The newly created HTTP session.
        """
        return self._create_http_session(self.post_adapter)

    @staticmethod
    def _create_http_session(adapter: HTTPAdapter) -> Session:
        """
        Create an HTTP session with the given adapter mounted.

        Args:
            adapter (HTTPAdapter): The adapter to mount to the HTTP session.

        Returns:
            Session: The newly created HTTP session.
        """
        http_session = requests.Session()
        http_session.mount("https://", adapter)
        http_session.mount("http://", adapter)
        return http_session

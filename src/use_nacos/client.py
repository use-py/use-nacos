"""Nacos client implementation.

This module provides synchronous and asynchronous clients for interacting
with Nacos server via Open API.
"""

import logging
import os
from abc import abstractmethod
from json import JSONDecodeError
from typing import Any, Dict, Generator, List, Optional, Union

import httpx
from httpx import AsyncHTTPTransport, Auth, HTTPTransport, Request, Response

from .endpoints import (
    ConfigAsyncEndpoint,
    ConfigEndpoint,
    InstanceAsyncEndpoint,
    InstanceEndpoint,
    NamespaceEndpoint,
    ServiceEndpoint,
)
from .exception import HTTPResponseError
from .typings import HttpxClient, SyncAsync

logger = logging.getLogger(__name__)

DEFAULT_SERVER_ADDR = "http://localhost:8848/"
DEFAULT_NAMESPACE = ""


class BaseClient:
    """Base class for Nacos clients.

    This class provides common functionality for both sync and async clients,
    including authentication, endpoint management, and request building.

    Attributes:
        server_addr: Nacos server address.
        username: Username for authentication.
        password: Password for authentication.
        namespace_id: Default namespace ID.
        config: Config endpoint for configuration management.
        instance: Instance endpoint for service instance management.
        service: Service endpoint for service management.
        namespace: Namespace endpoint for namespace management.
    """

    def __init__(
        self,
        client: HttpxClient,
        server_addr: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        namespace_id: Optional[str] = None,
    ) -> None:
        """Initialize the base client.

        Args:
            client: An httpx client instance (sync or async).
            server_addr: Nacos server address. Defaults to environment variable
                NACOS_SERVER_ADDR or "http://localhost:8848/".
            username: Username for authentication. Defaults to environment
                variable NACOS_USERNAME.
            password: Password for authentication. Defaults to environment
                variable NACOS_PASSWORD.
            namespace_id: Default namespace ID. Defaults to environment
                variable NACOS_NAMESPACE or empty string (public namespace).
        """
        self.server_addr = (
            server_addr or os.environ.get("NACOS_SERVER_ADDR") or DEFAULT_SERVER_ADDR
        )
        self.username = username or os.environ.get("NACOS_USERNAME")
        self.password = password or os.environ.get("NACOS_PASSWORD")
        self.namespace_id = (
            namespace_id or os.environ.get("NACOS_NAMESPACE") or DEFAULT_NAMESPACE
        )

        self._clients: List[HttpxClient] = []
        self.client = client
        # endpoints
        self.config = ConfigEndpoint(self)
        self.instance = InstanceEndpoint(self)
        self.service = ServiceEndpoint(self)
        self.namespace = NamespaceEndpoint(self)

    @property
    def client(self) -> HttpxClient:
        """Get the current httpx client instance.

        Returns:
            The current httpx client (sync or async).
        """
        return self._clients[-1]

    @client.setter
    def client(self, client: HttpxClient) -> None:
        """Set the httpx client with default configuration.

        Args:
            client: An httpx client instance to configure.
        """
        client.base_url = httpx.URL(self.server_addr)
        client.timeout = httpx.Timeout(timeout=60_000 / 1_000)
        client.headers = httpx.Headers(
            {
                "User-Agent": "use-py/use-nacos",
            }
        )
        self._clients.append(client)

    def _build_request(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Request:
        """Build an httpx Request object with the given parameters.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.).
            path: API endpoint path.
            query: Query parameters.
            body: Request body data.
            headers: Additional headers.
            **kwargs: Additional keyword arguments passed to build_request.

        Returns:
            An httpx Request object ready to be sent.
        """
        _headers = httpx.Headers()
        if headers:
            _headers.update(headers)
        return self.client.build_request(
            method, path, params=query, data=body, headers=_headers, **kwargs
        )

    @staticmethod
    def _parse_response(response: Response, serialized: bool) -> Any:
        """Parse the response body.

        Args:
            response: The httpx Response object.
            serialized: Whether to parse the response as JSON.

        Returns:
            Parsed response body (JSON dict, text string, or raw text).
        """
        if not serialized:
            return response.text
        try:
            body = response.json()
        except JSONDecodeError:
            body = response.text
        return body

    @abstractmethod
    def request(
        self,
        path: str,
        method: str,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> SyncAsync[Any]:
        """Send a request to the Nacos server.

        Args:
            path: API endpoint path.
            method: HTTP method.
            query: Query parameters.
            body: Request body data.
            headers: Additional headers.

        Returns:
            Response data from the server.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError


class NacosClient(BaseClient):
    """Synchronous Nacos client.

    This client provides a synchronous interface for interacting with Nacos
    server. Use this for traditional synchronous Python applications.

    Example:
        >>> with NacosClient(server_addr="http://localhost:8848") as client:
        ...     config = client.config.get("app.yaml", "DEFAULT_GROUP")
    """

    client: httpx.Client

    def __init__(
        self,
        server_addr: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        namespace_id: Optional[str] = None,
        client: Optional[httpx.Client] = None,
        *,
        http_retries: Optional[int] = 3,
    ) -> None:
        """Initialize the synchronous Nacos client.

        Args:
            server_addr: Nacos server address. Defaults to environment variable
                NACOS_SERVER_ADDR or "http://localhost:8848/".
            username: Username for authentication. Defaults to environment
                variable NACOS_USERNAME.
            password: Password for authentication. Defaults to environment
                variable NACOS_PASSWORD.
            namespace_id: Default namespace ID. Defaults to environment
                variable NACOS_NAMESPACE or empty string (public namespace).
            client: Custom httpx.Client instance. If not provided, a new one
                will be created.
            http_retries: Number of HTTP retry attempts. Defaults to 3.
        """
        client = client or httpx.Client(transport=HTTPTransport(retries=http_retries))
        super().__init__(
            client=client,
            server_addr=server_addr,
            username=username,
            password=password,
            namespace_id=namespace_id,
        )

    def request(
        self,
        path: str,
        method: str = "GET",
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        serialized: Optional[bool] = True,
        **kwargs: Any,
    ) -> Any:
        """Send a synchronous request to the Nacos server.

        Args:
            path: API endpoint path.
            method: HTTP method. Defaults to "GET".
            query: Query parameters.
            body: Request body data.
            headers: Additional headers.
            serialized: Whether to parse the response as JSON. Defaults to True.
            **kwargs: Additional keyword arguments passed to the request.

        Returns:
            Response data from the server.

        Raises:
            HTTPResponseError: If the server returns an error response.
        """
        request = self._build_request(method, path, query, body, headers, **kwargs)
        try:
            response = self.client.send(
                request, auth=NacosAPIAuth(self.username, self.password)
            )
            response.raise_for_status()
            return self._parse_response(response, serialized)  # type: ignore[arg-type]
        except httpx.HTTPStatusError as exc:
            raise HTTPResponseError(exc.response)


class NacosAsyncClient(BaseClient):
    """Asynchronous Nacos client.

    This client provides an asynchronous interface for interacting with Nacos
    server. Use this for async Python applications (FastAPI, asyncio, etc.).

    Example:
        >>> async with NacosAsyncClient(server_addr="http://localhost:8848") as client:
        ...     config = await client.config.get("app.yaml", "DEFAULT_GROUP")
    """

    client: httpx.AsyncClient

    def __init__(
        self,
        server_addr: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        namespace_id: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        *,
        http_retries: Optional[int] = 3,
    ) -> None:
        """Initialize the asynchronous Nacos client.

        Args:
            server_addr: Nacos server address. Defaults to environment variable
                NACOS_SERVER_ADDR or "http://localhost:8848/".
            username: Username for authentication. Defaults to environment
                variable NACOS_USERNAME.
            password: Password for authentication. Defaults to environment
                variable NACOS_PASSWORD.
            namespace_id: Default namespace ID. Defaults to environment
                variable NACOS_NAMESPACE or empty string (public namespace).
            client: Custom httpx.AsyncClient instance. If not provided, a new
                one will be created.
            http_retries: Number of HTTP retry attempts. Defaults to 3.
        """
        client = client or httpx.AsyncClient(
            transport=AsyncHTTPTransport(retries=http_retries)
        )
        super().__init__(
            client=client,
            server_addr=server_addr,
            username=username,
            password=password,
            namespace_id=namespace_id,
        )
        self.config = ConfigAsyncEndpoint(self)
        self.instance = InstanceAsyncEndpoint(self)

    async def request(
        self,
        path: str,
        method: str = "GET",
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        serialized: Optional[bool] = True,
        **kwargs: Any,
    ) -> Any:
        """Send an asynchronous request to the Nacos server.

        Args:
            path: API endpoint path.
            method: HTTP method. Defaults to "GET".
            query: Query parameters.
            body: Request body data.
            headers: Additional headers.
            serialized: Whether to parse the response as JSON. Defaults to True.
            **kwargs: Additional keyword arguments passed to the request.

        Returns:
            Response data from the server.

        Raises:
            HTTPResponseError: If the server returns an error response.
        """
        request = self._build_request(method, path, query, body, headers, **kwargs)
        try:
            response = await self.client.send(
                request, auth=NacosAPIAuth(self.username, self.password)
            )
            response.raise_for_status()
            return self._parse_response(response, serialized)  # type: ignore[arg-type]
        except httpx.HTTPStatusError as exc:
            raise HTTPResponseError(exc.response)


class NacosAPIAuth(Auth):
    """HTTP authentication for Nacos API.

    This authentication flow automatically injects username and password
    parameters into all requests.

    Attributes:
        auth_params: Authentication parameters (username, password).
    """

    def __init__(self, username: Optional[str], password: Optional[str]) -> None:
        """Initialize the Nacos API authentication.

        Args:
            username: Username for Nacos authentication.
            password: Password for Nacos authentication.
        """
        self.auth_params: Dict[str, Optional[str]] = {
            "username": username,
            "password": password,
        }

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        """Add authentication parameters to the request URL.

        Args:
            request: The HTTP request to authenticate.

        Yields:
            The modified request with auth parameters.
        """
        request.url = request.url.copy_merge_params(params=self.auth_params)  # type: ignore[arg-type]
        yield request

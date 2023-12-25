import logging
import os
from abc import abstractmethod
from json import JSONDecodeError
from typing import Any, Optional, Dict, List, Generator

import httpx
from httpx import Request, Response, Auth, HTTPTransport, AsyncHTTPTransport

from .endpoints import (
    ConfigEndpoint, InstanceEndpoint, ServiceEndpoint, NamespaceEndpoint,
    ConfigAsyncEndpoint, InstanceAsyncEndpoint
)
from .exception import HTTPResponseError
from .typings import SyncAsync, HttpxClient

logger = logging.getLogger(__name__)

DEFAULT_SERVER_ADDR = "http://localhost:8848/"
DEFAULT_NAMESPACE = ""


class BaseClient:

    def __init__(
            self,
            client: HttpxClient,
            server_addr: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            namespace_id: Optional[str] = None,
    ):
        self.server_addr = server_addr or os.environ.get("NACOS_SERVER_ADDR") or DEFAULT_SERVER_ADDR
        self.username = username or os.environ.get("NACOS_USERNAME")
        self.password = password or os.environ.get("NACOS_PASSWORD")
        self.namespace_id = namespace_id or os.environ.get("NACOS_NAMESPACE") or DEFAULT_NAMESPACE

        self._clients: List[HttpxClient] = []
        self.client = client
        # endpoints
        self.config = ConfigEndpoint(self)
        self.instance = InstanceEndpoint(self)
        self.service = ServiceEndpoint(self)
        self.namespace = NamespaceEndpoint(self)

    @property
    def client(self) -> HttpxClient:
        return self._clients[-1]

    @client.setter
    def client(self, client: HttpxClient) -> None:
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
            query: Optional[Dict[Any, Any]] = None,
            body: Optional[Dict[Any, Any]] = None,
            headers: Optional[Dict[Any, Any]] = None,
            **kwargs
    ) -> Request:
        _headers = httpx.Headers()
        if headers:
            _headers.update(headers)
        return self.client.build_request(
            method, path, params=query, data=body, headers=_headers, **kwargs
        )

    @staticmethod
    def _parse_response(response: Response, serialized: bool) -> Any:
        """ Parse response body """
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
            query: Optional[Dict[Any, Any]] = None,
            body: Optional[Dict[Any, Any]] = None,
            headers: Optional[Dict[Any, Any]] = None
    ) -> SyncAsync[Any]:
        raise NotImplementedError


class NacosClient(BaseClient):
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
    ):
        """ Nacos Sync Client """
        client = client or httpx.Client(transport=HTTPTransport(retries=http_retries))
        super().__init__(
            client=client,
            server_addr=server_addr,
            username=username,
            password=password,
            namespace_id=namespace_id
        )

    def request(
            self,
            path: str,
            method: str = "GET",
            query: Optional[Dict[Any, Any]] = None,
            body: Optional[Dict[Any, Any]] = None,
            headers: Optional[Dict[Any, Any]] = None,
            serialized: Optional[bool] = True,
            **kwargs
    ) -> Any:
        request = self._build_request(method, path, query, body, headers, **kwargs)
        try:
            response = self.client.send(
                request,
                auth=NacosAPIAuth(self.username, self.password)
            )
            response.raise_for_status()
            return self._parse_response(response, serialized)
        except httpx.HTTPStatusError as exc:
            raise HTTPResponseError(exc.response)


class NacosAsyncClient(BaseClient):
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
    ):
        """ Nacos Async Client """
        client = client or httpx.AsyncClient(transport=AsyncHTTPTransport(retries=http_retries))
        super().__init__(
            client=client,
            server_addr=server_addr,
            username=username,
            password=password,
            namespace_id=namespace_id
        )
        self.config = ConfigAsyncEndpoint(self)
        self.instance = InstanceAsyncEndpoint(self)

    async def request(
            self,
            path: str,
            method: str = "GET",
            query: Optional[Dict[Any, Any]] = None,
            body: Optional[Dict[Any, Any]] = None,
            headers: Optional[Dict[Any, Any]] = None,
            serialized: Optional[bool] = True,
            **kwargs
    ) -> Any:
        request = self._build_request(method, path, query, body, headers, **kwargs)
        try:
            response = await self.client.send(
                request,
                auth=NacosAPIAuth(self.username, self.password)
            )
            response.raise_for_status()
            return self._parse_response(response, serialized)
        except httpx.HTTPStatusError as exc:
            raise HTTPResponseError(exc.response)


class NacosAPIAuth(Auth):
    """ Attaches HTTP Nacos Authentication to the given Request object. """

    def __init__(
            self, username: str, password: str
    ) -> None:
        self.auth_params = {"username": username, "password": password}

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        request.url = request.url.copy_merge_params(params=self.auth_params)
        yield request

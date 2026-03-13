"""Service endpoint for Nacos naming service."""

import logging
from typing import Any, Optional

from ..typings import SyncAsync
from .endpoint import Endpoint

logger = logging.getLogger(__name__)


class ServiceEndpoint(Endpoint):
    """Service management endpoint for Nacos.

    This endpoint provides operations for managing services in Nacos,
    including creating, deleting, updating, and querying services.

    Example:
        >>> client = NacosClient()
        >>> # Create a service
        >>> client.service.create("my-service", namespace_id="dev")
        >>> # List all services
        >>> services = client.service.list(namespace_id="dev")
    """

    def create(
        self,
        service_name: str,
        namespace_id: Optional[str] = None,
        group_name: Optional[str] = None,
        protect_threshold: Optional[float] = 0,
        metadata: Optional[str] = None,
        selector: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Create a new service.

        Args:
            service_name: Name of the service to create.
            namespace_id: Namespace ID. Defaults to the client's namespace.
            group_name: Group name for the service.
            protect_threshold: Protection threshold (0.0 to 1.0).
                Defaults to 0.
            metadata: Service metadata as JSON string.
            selector: Selector configuration as JSON string.

        Returns:
            "ok" on success.

        Example:
            >>> client.service.create(
            ...     "my-service",
            ...     namespace_id="dev",
            ...     metadata='{"version":"1.0"}'
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/service",
            method="POST",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "protectThreshold": protect_threshold,
                "metadata": metadata,
                "selector": selector,
            },
        )

    def delete(
        self,
        service_name: str,
        namespace_id: Optional[str] = None,
        group_name: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Delete a service.

        Args:
            service_name: Name of the service to delete.
            namespace_id: Namespace ID. Defaults to the client's namespace.
            group_name: Group name for the service.

        Returns:
            "ok" on success.

        Example:
            >>> client.service.delete("my-service", namespace_id="dev")
        """
        return self.client.request(
            "/nacos/v1/ns/service",
            method="DELETE",
            query={
                "serviceName": service_name,
                "groupName": group_name,
                "namespaceId": namespace_id,
            },
        )

    def list(
        self,
        page_no: Optional[int] = 1,
        page_size: Optional[int] = 20,
        namespace_id: Optional[str] = None,
        group_name: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """List services with pagination.

        Args:
            page_no: Page number (1-indexed). Defaults to 1.
            page_size: Number of items per page. Defaults to 20.
            namespace_id: Namespace ID. Defaults to the client's namespace.
            group_name: Group name to filter by.

        Returns:
            A dict containing:
                - count: Total number of services
                - doms: List of service names

        Example:
            >>> result = client.service.list(namespace_id="dev")
            >>> print(result["count"], result["doms"])
        """
        return self.client.request(
            "/nacos/v1/ns/service/list",
            query={
                "pageNo": page_no,
                "pageSize": page_size,
                "namespaceId": namespace_id,
                "groupName": group_name,
            },
        )

    def update(
        self,
        service_name: str,
        namespace_id: Optional[str] = None,
        group_name: Optional[str] = None,
        protect_threshold: Optional[float] = None,
        metadata: Optional[str] = None,
        selector: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Update a service's configuration.

        Args:
            service_name: Name of the service to update.
            namespace_id: Namespace ID. Defaults to the client's namespace.
            group_name: Group name for the service.
            protect_threshold: Protection threshold (0.0 to 1.0).
            metadata: Service metadata as JSON string.
            selector: Selector configuration as JSON string.

        Returns:
            "ok" on success.

        Example:
            >>> client.service.update(
            ...     "my-service",
            ...     namespace_id="dev",
            ...     protect_threshold=0.5
            ... )
        """
        return self.client.request(
            "/nacos/v1/ns/service",
            method="PUT",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "protectThreshold": protect_threshold,
                "metadata": metadata,
                "selector": selector,
            },
        )

    def get(
        self,
        service_name: str,
        namespace_id: Optional[str] = "",
        group_name: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Get service details.

        Args:
            service_name: Name of the service to query.
            namespace_id: Namespace ID. Defaults to the client's namespace.
            group_name: Group name for the service.

        Returns:
            A dict containing service details including:
                - name: Service name
                - groupName: Group name
                - clusters: List of clusters
                - protectThreshold: Protection threshold
                - metadata: Service metadata

        Example:
            >>> service = client.service.get("my-service", namespace_id="dev")
            >>> print(service["name"])
        """
        return self.client.request(
            "/nacos/v1/ns/service",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "groupName": group_name,
            },
        )

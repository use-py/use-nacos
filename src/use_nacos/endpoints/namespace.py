"""Namespace endpoint for Nacos console API."""

import logging
from typing import Any, Optional

from ..typings import SyncAsync
from .endpoint import Endpoint

logger = logging.getLogger(__name__)


class NamespaceEndpoint(Endpoint):
    """Namespace management endpoint for Nacos.

    This endpoint provides operations for managing namespaces in Nacos,
    including creating, deleting, updating, and listing namespaces.

    Example:
        >>> client = NacosClient()
        >>> # Create a namespace
        >>> client.namespace.create("dev", "Development")
        >>> # List all namespaces
        >>> namespaces = client.namespace.list()
    """

    def create(
        self,
        custom_namespace_id: str,
        namespace_name: str,
        namespace_desc: Optional[str] = None,
    ) -> SyncAsync[Any]:
        """Create a new namespace.

        Args:
            custom_namespace_id: Custom namespace ID (user-defined).
            namespace_name: Display name for the namespace.
            namespace_desc: Description of the namespace.

        Returns:
            "ok" on success.

        Example:
            >>> client.namespace.create(
            ...     custom_namespace_id="dev",
            ...     namespace_name="Development",
            ...     namespace_desc="Development environment"
            ... )
        """
        return self.client.request(
            "/nacos/v1/console/namespaces",
            method="POST",
            query={
                "customNamespaceId": custom_namespace_id,
                "namespaceName": namespace_name,
                "namespaceDesc": namespace_desc,
            },
        )

    def delete(self, namespace_id: str) -> SyncAsync[Any]:
        """Delete a namespace.

        Args:
            namespace_id: ID of the namespace to delete.

        Returns:
            "ok" on success.

        Warning:
            Deleting a namespace will also delete all services and configurations
            within that namespace.

        Example:
            >>> client.namespace.delete("dev")
        """
        return self.client.request(
            "/nacos/v1/console/namespaces",
            method="DELETE",
            query={"namespaceId": namespace_id},
        )

    def list(self) -> SyncAsync[Any]:
        """List all namespaces.

        Returns:
            A dict containing:
                - data: List of namespace objects with id, name, desc, etc.

        Example:
            >>> namespaces = client.namespace.list()
            >>> for ns in namespaces["data"]:
            ...     print(ns["namespace"], ns["namespaceShowName"])
        """
        return self.client.request("/nacos/v1/console/namespaces")

    def update(
        self, namespace: str, namespace_show_name: str, namespace_desc: str
    ) -> SyncAsync[Any]:
        """Update a namespace's configuration.

        Args:
            namespace: Namespace ID to update.
            namespace_show_name: New display name for the namespace.
            namespace_desc: New description for the namespace.

        Returns:
            "ok" on success.

        Example:
            >>> client.namespace.update(
            ...     namespace="dev",
            ...     namespace_show_name="Development",
            ...     namespace_desc="Updated description"
            ... )
        """
        return self.client.request(
            "/nacos/v1/console/namespaces",
            method="PUT",
            query={
                "namespace": namespace,
                "namespaceShowName": namespace_show_name,
                "namespaceDesc": namespace_desc,
            },
        )

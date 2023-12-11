import logging
from typing import Optional, Any

from .endpoint import Endpoint
from ..typings import SyncAsync

logger = logging.getLogger(__name__)


class NamespaceEndpoint(Endpoint):
    """ Namespace Management API """

    def create(
            self,
            custom_namespace_id: str,
            namespace_name: str,
            namespace_desc: Optional[str] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/console/namespaces",
            method="POST",
            query={
                "customNamespaceId": custom_namespace_id,
                "namespaceName": namespace_name,
                "namespaceDesc": namespace_desc
            }
        )

    def delete(
            self,
            namespace_id: str,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/console/namespaces",
            method="DELETE",
            query={
                "namespaceId": namespace_id
            }
        )

    def list(self) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/console/namespaces"
        )

    def update(
            self,
            namespace: str,
            namespace_show_name: str,
            namespace_desc: str
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/console/namespaces",
            method="PUT",
            query={
                "namespace": namespace,
                "namespaceShowName": namespace_show_name,
                "namespaceDesc": namespace_desc
            }
        )

import logging
from typing import Optional, Any

from .endpoint import Endpoint
from ..typings import SyncAsync

logger = logging.getLogger(__name__)


class ServiceEndpoint(Endpoint):
    """ Service Management API """

    def create(
            self,
            service_name: str,
            namespace_id: Optional[str] = None,
            group_name: Optional[str] = None,
            protect_threshold: Optional[float] = 0,
            metadata: Optional[str] = None,
            selector: Optional[str] = None,
    ) -> SyncAsync[Any]:
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
            }
        )

    def delete(
            self,
            service_name: str,
            namespace_id: Optional[str] = None,
            group_name: Optional[str] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/service",
            method="DELETE",
            query={
                "serviceName": service_name,
                "groupName": group_name,
                "namespaceId": namespace_id
            }
        )

    def list(
            self,
            page_no: Optional[int] = 1,
            page_size: Optional[int] = 20,
            namespace_id: Optional[str] = None,
            group_name: Optional[str] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/service/list",
            query={
                "pageNo": page_no,
                "pageSize": page_size,
                "namespaceId": namespace_id,
                "groupName": group_name,
            }
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
            }
        )

    def get(
            self,
            service_name: str,
            namespace_id: Optional[str] = '',
            group_ame: Optional[str] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/service",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "groupName": group_ame,
            }
        )

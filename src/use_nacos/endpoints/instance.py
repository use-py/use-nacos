import asyncio
import json
import logging
import threading
import time
from typing import Optional, Any, Literal

from .endpoint import Endpoint
from .._chooser import Chooser
from ..typings import SyncAsync, BeatType

_ConsistencyType = Literal["ephemeral", "persist"]

logger = logging.getLogger(__name__)


class InstanceOperationMixin:

    def heartbeat(
            self,
            service_name: str,
            ip: str,
            port: int,
            weight: Optional[float] = 1.0,
            namespace_id: Optional[str] = '',
            group_name: Optional[str] = None,
            ephemeral: Optional[bool] = True,
            interval: Optional[int] = 1_000,
            skip_exception: Optional[bool] = True,
            **kwargs
    ) -> SyncAsync[Any]:
        stop_event = threading.Event()
        stop_event.cancel = stop_event.set

        def _heartbeat():
            while not stop_event.is_set():
                time.sleep(interval / 1_000)
                try:
                    self.beat(
                        service_name=service_name,
                        ip=ip,
                        port=port,
                        weight=weight,
                        namespace_id=namespace_id,
                        group_name=group_name,
                        ephemeral=ephemeral,
                        **kwargs
                    )
                except Exception as exc:
                    logger.error("Heartbeat error: %s", exc)
                    if skip_exception:
                        continue
                    raise exc

        thread = threading.Thread(target=_heartbeat)
        thread.start()
        return stop_event

    def get_one_healthy(
            self,
            service_name: str,
            namespace_id: Optional[str] = None,
            group_name: Optional[str] = None,
            clusters: Optional[str] = None,

    ):
        """ Get a healthy instance """
        instances = self.list(
            service_name=service_name,
            namespace_id=namespace_id,
            group_name=group_name,
            clusters=clusters,
            healthy_only=True
        )
        hosts = [
            (host, host.get('weight'))
            for host in instances["hosts"]
        ]
        chooser = Chooser(hosts)
        chooser.refresh()
        return chooser.random_with_weight()


class InstanceAsyncOperationMixin:

    async def heartbeat(
            self,
            service_name: str,
            ip: str,
            port: int,
            weight: Optional[float] = 1.0,
            namespace_id: Optional[str] = '',
            group_name: Optional[str] = None,
            ephemeral: Optional[bool] = True,
            interval: Optional[int] = 1_000,
            skip_exception: Optional[bool] = True,
            **kwargs
    ) -> SyncAsync[Any]:
        stop_event = threading.Event()
        stop_event.cancel = stop_event.set

        async def _async_heartbeat():
            while True:
                await asyncio.sleep(interval / 1_000)
                try:
                    await self.beat(
                        service_name=service_name,
                        ip=ip,
                        port=port,
                        weight=weight,
                        namespace_id=namespace_id,
                        group_name=group_name,
                        ephemeral=ephemeral,
                        **kwargs
                    )
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.error("Heartbeat error: %s", exc)
                    if skip_exception:
                        continue
                    raise exc

        return asyncio.create_task(_async_heartbeat())

    async def get_one_healthy(
            self,
            service_name: str,
            namespace_id: Optional[str] = None,
            group_name: Optional[str] = None,
            clusters: Optional[str] = None,

    ):
        """ Get a healthy instance """
        instances = await self.list(
            service_name=service_name,
            namespace_id=namespace_id,
            group_name=group_name,
            clusters=clusters,
            healthy_only=True
        )
        hosts = [
            (host, host.get('weight'))
            for host in instances["hosts"]
        ]
        chooser = Chooser(hosts)
        chooser.refresh()
        return chooser.random_with_weight()


class _BaseInstanceEndpoint(Endpoint):
    """ Instance Management API """

    def register(
            self,
            service_name: str,
            ip: str,
            port: int,
            namespace_id: Optional[str] = '',
            weight: Optional[float] = 1.0,
            enabled: Optional[bool] = True,
            healthy: Optional[bool] = True,
            metadata: Optional[str] = None,
            cluster_name: Optional[str] = None,
            group_name: Optional[str] = None,
            ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        """ Register instance """

        return self.client.request(
            "/nacos/v1/ns/instance",
            method="POST",
            query={
                "ip": ip,
                "port": port,
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "weight": weight,
                "enabled": enabled,
                "healthy": healthy,
                "metadata": metadata,
                "clusterName": cluster_name,
                "groupName": group_name,
                "ephemeral": ephemeral,
            }
        )

    def delete(
            self,
            service_name: str,
            ip: str,
            port: str,
            group_name: Optional[str] = None,
            cluster_name: Optional[str] = None,
            namespace_id: Optional[str] = None,
            ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/instance",
            method="DELETE",
            query={
                "serviceName": service_name,
                "ip": ip,
                "port": port,
                "groupName": group_name,
                "clusterName": cluster_name,
                "namespaceId": namespace_id,
                "ephemeral": ephemeral,
            }
        )

    def list(
            self,
            service_name: str,
            namespace_id: Optional[str] = None,
            group_name: Optional[str] = None,
            clusters: Optional[str] = None,
            healthy_only: Optional[bool] = False,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/instance/list",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "clusters": clusters,
                "healthyOnly": healthy_only,
            }
        )

    def update(
            self,
            service_name: str,
            ip: str,
            port: int,
            namespace_id: Optional[str] = None,
            weight: Optional[float] = None,
            enabled: Optional[bool] = None,
            metadata: Optional[dict] = None,
            cluster_name: Optional[str] = None,
            group_name: Optional[str] = None,
            ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/instance",
            method="PUT",
            query={
                "ip": ip,
                "port": port,
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "weight": weight,
                "enabled": enabled,
                "metadata": metadata,
                "clusterName": cluster_name,
                "groupName": group_name,
                "ephemeral": ephemeral,
            }
        )

    def get(
            self,
            service_name: str,
            ip: str,
            port: int,
            namespace_id: Optional[str] = '',
            group_name: Optional[str] = None,
            cluster: Optional[str] = None,
            healthy_only: Optional[bool] = False,
            ephemeral: Optional[bool] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/instance",
            query={
                "serviceName": service_name,
                "ip": ip,
                "port": port,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "cluster": cluster,
                "healthyOnly": healthy_only,
                "ephemeral": ephemeral,
            }
        )

    def beat(
            self,
            service_name: str,
            ip: str,
            port: int,
            weight: Optional[float] = 1.0,
            namespace_id: Optional[str] = '',
            group_name: Optional[str] = None,
            ephemeral: Optional[bool] = None,
            **kwargs
    ) -> SyncAsync[Any]:
        # see: https://github.com/alibaba/nacos/issues/10448#issuecomment-1538178112
        serverName = f"{group_name}@@{service_name}" if group_name else service_name
        beat_params: BeatType = {
            "serviceName": serverName,
            "ip": ip,
            "port": port,
            "weight": weight,
            "ephemeral": ephemeral,
            **kwargs
        }
        return self.client.request(
            "/nacos/v1/ns/instance/beat",
            method="PUT",
            query={
                "serviceName": serverName,
                "beat": json.dumps(beat_params),
                "namespaceId": namespace_id,
                "groupName": group_name,
            }
        )

    def update_health(
            self,
            service_name: str,
            ip: str,
            port: int,
            healthy: bool,
            namespace_id: Optional[str] = '',
            group_name: Optional[str] = None,
            cluster_name: Optional[str] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/health/instance",
            method="PUT",
            query={
                "serviceName": service_name,
                "ip": ip,
                "port": port,
                "healthy": healthy,
                "namespaceId": namespace_id,
                "groupName": group_name,
                "clusterName": cluster_name,
            }
        )

    def batch_update_metadata(
            self,
            service_name: str,
            namespace_id: str,
            metadata: dict,
            consistency_type: Optional["_ConsistencyType"] = None,
            instances: Optional[list] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/instance/metadata/batch",
            method="PUT",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "metadata": json.dumps(metadata),
                "consistencyType": consistency_type,
                "instances": json.dumps(instances),
            }
        )

    def batch_delete_metadata(
            self,
            service_name: str,
            namespace_id: str,
            metadata: dict,
            consistency_type: Optional["_ConsistencyType"] = None,
            instances: Optional[list] = None,
    ) -> SyncAsync[Any]:
        return self.client.request(
            "/nacos/v1/ns/instance/metadata/batch",
            method="DELETE",
            query={
                "serviceName": service_name,
                "namespaceId": namespace_id,
                "metadata": json.dumps(metadata),
                "consistencyType": consistency_type,
                "instances": json.dumps(instances),
            }
        )


class InstanceEndpoint(_BaseInstanceEndpoint, InstanceOperationMixin):
    ...


class InstanceAsyncEndpoint(_BaseInstanceEndpoint, InstanceAsyncOperationMixin):
    ...

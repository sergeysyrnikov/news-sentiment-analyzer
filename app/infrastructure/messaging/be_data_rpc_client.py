"""Infrastructure NATS RPC client for BE-data service (request/reply)."""

from __future__ import annotations

from aiologger import Logger  # type: ignore[import-untyped]

from app.core.config.nats import NATSSettings
from app.domain.interfaces.services.be_data_rpc_client import IBeDataRpcClient
from app.infrastructure.messaging.nats_base_rpc_client import BaseNatsRpcClient


class BeDataRpcClient(BaseNatsRpcClient, IBeDataRpcClient):
    """Core NATS request/reply client for BE-data."""

    def __init__(
        self,
        *,
        settings: NATSSettings,
        logger: Logger,
    ) -> None:
        super().__init__(
            settings=settings,
            client_name="bf-service-be-data-rpc-client",
            logger=logger,
        )
        self._logger = logger

    # async def get_user_delivery_channels(self, *, payload: dict[str, Any]) -> Any:
    #     try:
    #         response = await self._request(
    #             subject=self._settings.be_data_rpc_subject,
    #             action="get_user_delivery_channels",
    #             payload=payload,
    #             timeout=self._settings.be_data_rpc_timeout_sec,
    #             component="be_data_rpc_client",
    #         )
    #     except Exception as exc:
    #         raise ExternalServiceError("be-data", str(exc)) from exc

    #     if response.get("ok") is True:
    #         return response.get("data")

    #     error = response.get("error") or {}
    #     raise ExternalServiceError("be-data", error.get("message", "Unknown NATS RPC error"))

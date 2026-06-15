"""Infrastructure base for NATS RPC clients with lazy connect policy."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import nats
from aiologger import Logger  # type: ignore[import-untyped]
from nats.aio.client import Client as NATSClient

from app.core.config.nats import NATSSettings


class BaseNatsRpcClient:
    """Reusable base NATS RPC client with lazy connect + reconnect policy."""

    def __init__(
        self,
        *,
        settings: NATSSettings,
        client_name: str,
        logger: Logger | None = None,
    ) -> None:
        self._settings = settings
        self._client: NATSClient | None = None
        self._lock = asyncio.Lock()
        self._client_name = client_name
        self._logger = logger

    async def _request(
        self,
        *,
        subject: str,
        action: str,
        payload: dict[str, Any],
        timeout: float,
        component: str,
    ) -> dict[str, Any]:
        """Perform core NATS request/reply and parse JSON response."""
        client = await self._ensure_client()
        try:
            msg = await client.request(
                subject,
                json.dumps(
                    {"action": action, "payload": payload},
                    default=str,
                ).encode(),
                timeout=timeout,
            )
            decoded: Any = json.loads(msg.data.decode())
        except Exception:
            logger = self._logger
            if logger is not None:
                await logger.warning(
                    "NATS RPC request failed",
                    extra={
                        "component": component,
                        "subject": subject,
                        "action": action,
                    },
                    exc_info=True,
                )
            raise

        if isinstance(decoded, dict):
            return decoded
        raise ValueError("Invalid RPC response: expected JSON object")

    async def _ensure_client(self) -> NATSClient:
        client = self._client
        if client is not None and client.is_connected:
            return client

        async with self._lock:
            client = self._client
            if client is not None and client.is_connected:
                return client

            max_retries = 5
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    client = await nats.connect(
                        self._settings.hosts,
                        name=self._client_name,
                        verbose=False,
                        allow_reconnect=True,
                        max_reconnect_attempts=-1,
                        reconnect_time_wait=2,
                    )
                    self._client = client
                    return client
                except Exception as exc:
                    if attempt < max_retries - 1:
                        if self._logger is not None:
                            await self._logger.warning(
                                "Failed to connect to NATS "
                                f"(attempt {attempt + 1}/{max_retries}), "
                                f"retrying in {retry_delay}s: {exc}",
                                extra={
                                    "component": "nats_base_rpc_client",
                                    "client_name": self._client_name,
                                    "attempt": attempt + 1,
                                },
                            )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        if self._logger is not None:
                            await self._logger.error(
                                f"Failed to connect to NATS after {max_retries} attempts: {exc}",
                                extra={
                                    "component": "nats_base_rpc_client",
                                    "client_name": self._client_name,
                                },
                                exc_info=True,
                            )
                        raise

            raise ConnectionError("Failed to connect to NATS")

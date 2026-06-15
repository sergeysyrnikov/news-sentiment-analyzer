"""Core NATS RPC server (request/reply)."""

from __future__ import annotations

import asyncio
from typing import Optional

import nats
from aiologger import Logger  # type: ignore
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription

from app.core.config.nats import NATSSettings
from app.domain.interfaces.messaging.rpc_message_handler import IRpcMessageHandler


class NatsRpcServer:
    """Subscribe to core NATS subjects and dispatch request/reply messages.

    This component is intentionally separated from JetStream consumer logic.
    """

    def __init__(
        self,
        *,
        settings: NATSSettings,
        logger: Logger,
        message_handler: IRpcMessageHandler | None = None,
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._message_handler = message_handler
        self._nats_client: Optional[NATSClient] = None
        self._sub: Subscription | None = None

    def set_message_handler(self, handler: IRpcMessageHandler) -> None:
        """Set message handler for processing RPC messages."""
        self._message_handler = handler

    async def start(self) -> None:
        """Connect to NATS and subscribe to configured RPC subject."""
        subject = (self._settings.rpc_subject or "").strip()
        if not subject:
            await self._logger.info(
                "RPC subject is empty, NatsRpcServer is disabled",
                extra={"component": "nats_rpc_server"},
            )
            return

        max_retries = 4
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                self._nats_client = await nats.connect(
                    self._settings.hosts,
                    name="bf-service-rpc",
                    verbose=False,
                    allow_reconnect=True,
                    max_reconnect_attempts=-1,
                    reconnect_time_wait=2,
                )

                async def _cb(msg: Msg) -> None:
                    await self._handle_message(msg)

                queue = (self._settings.rpc_queue or "").strip()
                if queue:
                    self._sub = await self._nats_client.subscribe(
                        subject,
                        queue=queue,
                        cb=_cb,
                    )
                else:
                    self._sub = await self._nats_client.subscribe(
                        subject,
                        cb=_cb,
                    )

                await self._logger.info(
                    f"Subscribed to RPC subject {subject}",
                    extra={
                        "component": "nats_rpc_server",
                        "subject": subject,
                        "queue": queue or None,
                    },
                )

                await self._logger.info(
                    "NatsRpcServer started",
                    extra={"component": "nats_rpc_server"},
                )
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    await self._logger.warning(
                        f"Failed to connect to NATS "
                        f"(attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay}s: {e}",
                        extra={"component": "nats_rpc_server", "attempt": attempt + 1},
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    await self._logger.error(
                        f"Failed to start NatsRpcServer after {max_retries} attempts: {e}",
                        extra={"component": "nats_rpc_server"},
                        exc_info=True,
                    )
                    raise

    async def stop(self) -> None:
        """Unsubscribe and close NATS connection."""
        if self._sub is not None:
            try:
                await self._sub.unsubscribe()
            except Exception:
                await self._logger.warning(
                    "Failed to unsubscribe RPC subscription",
                    extra={"component": "nats_rpc_server"},
                    exc_info=True,
                )
            self._sub = None

        if self._nats_client:
            await self._nats_client.close()
            self._nats_client = None
            await self._logger.info(
                "NatsRpcServer stopped",
                extra={"component": "nats_rpc_server"},
            )

    async def _handle_message(self, msg: Msg) -> None:
        """Dispatch incoming RPC message to message handler."""
        if self._message_handler is None:
            await self._logger.error(
                "Message handler is not configured",
                extra={"component": "nats_rpc_server"},
            )
            return
        await self._message_handler.handle(msg=msg)

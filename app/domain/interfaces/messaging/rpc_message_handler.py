"""RPC Message handler interface."""

from abc import ABC, abstractmethod

from nats.aio.msg import Msg


class IRpcMessageHandler(ABC):
    """Interface for RPC message handlers."""

    @abstractmethod
    async def handle(self, *, msg: Msg) -> None:
        """Handle incoming RPC message."""
        pass

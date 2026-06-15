from unittest.mock import AsyncMock

import pytest
from nats.aio.msg import Msg

from app.core.config.nats import NATSSettings
from app.infrastructure.messaging.nats_rpc_server import NatsRpcServer


@pytest.fixture
def nats_settings():
    return NATSSettings(
        hosts="nats://localhost:4222",
        rpc_subject="bf_service.rpc",
        rpc_queue="bf_service_queue",
        be_data_rpc_subject="be_data.rpc",
    )


@pytest.fixture
def mock_logger():
    logger = AsyncMock()
    logger.info = AsyncMock()
    logger.warning = AsyncMock()
    logger.error = AsyncMock()
    return logger


@pytest.mark.asyncio
async def test_start_success(mocker, nats_settings, mock_logger):
    mock_connect = mocker.patch("nats.connect", new_callable=AsyncMock)
    mock_nats_client = AsyncMock()
    mock_connect.return_value = mock_nats_client

    server = NatsRpcServer(settings=nats_settings, logger=mock_logger)

    await server.start()

    mock_connect.assert_called_once()
    mock_nats_client.subscribe.assert_called_once()
    args, kwargs = mock_nats_client.subscribe.call_args
    assert args[0] == nats_settings.rpc_subject
    assert kwargs["queue"] == nats_settings.rpc_queue


@pytest.mark.asyncio
async def test_start_disabled(mocker, mock_logger):
    settings = NATSSettings(hosts="nats://localhost:4222", rpc_subject="")
    mock_connect = mocker.patch("nats.connect", new_callable=AsyncMock)

    server = NatsRpcServer(settings=settings, logger=mock_logger)

    await server.start()

    mock_connect.assert_not_called()
    mock_logger.info.assert_called_with(
        "RPC subject is empty, NatsRpcServer is disabled", extra={"component": "nats_rpc_server"}
    )


@pytest.mark.asyncio
async def test_stop_success(mocker, nats_settings, mock_logger):
    server = NatsRpcServer(settings=nats_settings, logger=mock_logger)

    mock_sub = AsyncMock()
    mock_nats_client = AsyncMock()
    server._sub = mock_sub
    server._nats_client = mock_nats_client

    await server.stop()

    mock_sub.unsubscribe.assert_called_once()
    mock_nats_client.close.assert_called_once()
    assert server._sub is None
    assert server._nats_client is None


@pytest.mark.asyncio
async def test_handle_message(mocker, nats_settings, mock_logger):
    mock_handler = AsyncMock()
    server = NatsRpcServer(settings=nats_settings, logger=mock_logger, message_handler=mock_handler)

    msg = AsyncMock(spec=Msg)
    await server._handle_message(msg)

    mock_handler.handle.assert_called_once_with(msg=msg)


@pytest.mark.asyncio
async def test_handle_message_no_handler(mocker, nats_settings, mock_logger):
    server = NatsRpcServer(settings=nats_settings, logger=mock_logger)

    msg = AsyncMock(spec=Msg)
    await server._handle_message(msg)

    mock_logger.error.assert_called_once_with(
        "Message handler is not configured", extra={"component": "nats_rpc_server"}
    )

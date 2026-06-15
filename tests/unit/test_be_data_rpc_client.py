import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config.nats import NATSSettings
from app.infrastructure.messaging.nats_base_rpc_client import BaseNatsRpcClient


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
    logger.warning = AsyncMock()
    logger.error = AsyncMock()
    return logger


@pytest.mark.asyncio
async def test_ensure_client_success(mocker, nats_settings, mock_logger):
    mock_connect = mocker.patch("nats.connect", new_callable=AsyncMock)
    mock_nats_client = AsyncMock()
    mock_connect.return_value = mock_nats_client

    client = BaseNatsRpcClient(settings=nats_settings, client_name="test_client", logger=mock_logger)

    res = await client._ensure_client()

    assert res is mock_nats_client
    mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_request_success(mocker, nats_settings, mock_logger):
    client = BaseNatsRpcClient(settings=nats_settings, client_name="test_client", logger=mock_logger)

    mock_nats_client = AsyncMock()
    # mock _ensure_client to return our mock nats client
    mocker.patch.object(client, "_ensure_client", return_value=mock_nats_client)

    # Mock response
    mock_msg = MagicMock()
    mock_msg.data = json.dumps({"ok": True, "data": {"key": "value"}}).encode()
    mock_nats_client.request.return_value = mock_msg

    response = await client._request(
        subject="test.subject", action="test_action", payload={"arg": 1}, timeout=1.0, component="test_component"
    )

    assert response == {"ok": True, "data": {"key": "value"}}
    mock_nats_client.request.assert_called_once()
    args, kwargs = mock_nats_client.request.call_args
    assert args[0] == "test.subject"
    req_data = json.loads(args[1].decode())
    assert req_data["action"] == "test_action"
    assert req_data["payload"] == {"arg": 1}
    assert kwargs["timeout"] == 1.0

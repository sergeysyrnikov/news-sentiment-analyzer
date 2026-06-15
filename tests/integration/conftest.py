from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.app import app


@pytest.fixture
def client(mock_async_logger):
    mock_server = AsyncMock()
    app.container.nats_rpc_server.override(mock_server)
    app.container.logger.override(mock_async_logger)

    with TestClient(app) as test_client:
        yield test_client

    app.container.nats_rpc_server.reset_override()
    app.container.logger.reset_override()


@pytest.fixture
def container():
    return app.container

import json
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from app.domain.exceptions import DependencyConflictError, EntityNotFoundError
from app.infrastructure.messaging.rpc_message_handler import RpcMessageHandler


class MockMsg:
    def __init__(self, data: bytes):
        self.data = data
        self.respond = AsyncMock()


class MockModel(BaseModel):
    id: int
    name: str


@pytest.fixture
def mock_logger():
    logger = AsyncMock()
    logger.info = AsyncMock()
    logger.debug = AsyncMock()
    logger.error = AsyncMock()
    return logger


@pytest.fixture
def mock_health_service():
    service = AsyncMock()
    service.check.return_value = {"status": "up"}
    return service


@pytest.fixture
def handler(mock_logger, mock_health_service):
    db_mock = AsyncMock()
    return RpcMessageHandler(logger=mock_logger, health_service=mock_health_service, db=db_mock)


@pytest.mark.asyncio
async def test_rpc_handle_success(handler, mock_health_service):
    msg = MockMsg(data=json.dumps({"action": "health_check", "payload": {}}).encode())
    await handler.handle(msg=msg)

    mock_health_service.check.assert_called_once()
    msg.respond.assert_called_once()

    # Check the response structure
    args, _ = msg.respond.call_args
    resp = json.loads(args[0].decode())
    assert resp["ok"] is True
    assert resp["data"] == {"status": "up"}


@pytest.mark.asyncio
async def test_rpc_handle_missing_action(handler):
    msg = MockMsg(data=json.dumps({"payload": {}}).encode())
    await handler.handle(msg=msg)

    msg.respond.assert_called_once()
    args, _ = msg.respond.call_args
    resp = json.loads(args[0].decode())
    assert resp["ok"] is False
    assert resp["error"]["code"] == "MISSING_ACTION"
    assert resp["error"]["status_code"] == 400


@pytest.mark.asyncio
async def test_rpc_handle_unknown_action(handler):
    msg = MockMsg(data=json.dumps({"action": "unknown", "payload": {}}).encode())
    await handler.handle(msg=msg)

    msg.respond.assert_called_once()
    args, _ = msg.respond.call_args
    resp = json.loads(args[0].decode())
    assert resp["ok"] is False
    assert resp["error"]["code"] == "UNKNOWN_ACTION"
    assert resp["error"]["status_code"] == 400


@pytest.mark.asyncio
async def test_rpc_handle_entity_not_found_error(handler, mock_health_service):
    mock_health_service.check.side_effect = EntityNotFoundError(message="Not found", code="NOT_FOUND")
    msg = MockMsg(data=json.dumps({"action": "health_check", "payload": {}}).encode())

    await handler.handle(msg=msg)

    args, _ = msg.respond.call_args
    resp = json.loads(args[0].decode())
    assert resp["ok"] is False
    assert resp["error"]["code"] == "NOT_FOUND"
    assert resp["error"]["status_code"] == 404


@pytest.mark.asyncio
async def test_rpc_handle_dependency_conflict_error(handler, mock_health_service):
    mock_health_service.check.side_effect = DependencyConflictError(message="Conflict", code="CONFLICT")
    msg = MockMsg(data=json.dumps({"action": "health_check", "payload": {}}).encode())

    await handler.handle(msg=msg)

    args, _ = msg.respond.call_args
    resp = json.loads(args[0].decode())
    assert resp["ok"] is False
    assert resp["error"]["code"] == "CONFLICT"
    assert resp["error"]["status_code"] == 409


@pytest.mark.asyncio
async def test_rpc_handle_internal_error(handler, mock_health_service):
    mock_health_service.check.side_effect = ValueError("Some internal issue")
    msg = MockMsg(data=json.dumps({"action": "health_check", "payload": {}}).encode())

    await handler.handle(msg=msg)

    args, _ = msg.respond.call_args
    resp = json.loads(args[0].decode())
    assert resp["ok"] is False
    assert resp["error"]["code"] == "INTERNAL_ERROR"
    assert resp["error"]["status_code"] == 500


def test_result_to_jsonable_model():
    model = MockModel(id=1, name="test")
    res = RpcMessageHandler._result_to_jsonable(model)
    assert res == {"id": 1, "name": "test"}


def test_result_to_jsonable_list():
    models = [MockModel(id=1, name="test"), MockModel(id=2, name="test2")]
    res = RpcMessageHandler._result_to_jsonable(models)
    assert res == [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]

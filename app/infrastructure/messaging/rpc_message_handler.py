"""Core NATS RPC message handler implementation."""

from __future__ import annotations

import json
from typing import Any

from aiologger import Logger  # type: ignore
from nats.aio.msg import Msg
from pydantic import ValidationError

from app.application.services.health_service import HealthService
from app.domain.exceptions import DependencyConflictError, DomainException, EntityNotFoundError
from app.domain.interfaces.messaging.rpc_message_handler import IRpcMessageHandler
from app.infrastructure.persistence.database import DatabaseManager


class RpcMessageHandler(IRpcMessageHandler):
    """NATS RPC handler: parse request envelope, dispatch by ``action``, respond with JSON."""

    def __init__(
        self,
        logger: Logger,
        health_service: HealthService,
        db: DatabaseManager,
    ) -> None:
        self._logger = logger
        self._health_service = health_service
        self._db = db

    async def handle(self, *, msg: Msg) -> None:
        """Handle NATS RPC message and respond via request/reply."""
        try:
            request = json.loads(msg.data.decode())
            action = request.get("action")
            payload = request.get("payload") or {}
            data = await self._dispatch(action=action, payload=payload)
            safe = self._result_to_jsonable(data)
            await msg.respond(json.dumps({"ok": True, "data": safe}, default=str).encode())
            await self._logger.debug(
                f"NATS RPC message handled successfully (action={action!r})",
                extra={"component": "message_handler", "action": action},
            )
        except EntityNotFoundError as exc:
            await msg.respond(self._error_response(exc.message, 404, exc.code))
        except DependencyConflictError as exc:
            await msg.respond(self._error_response(exc.message, 409, exc.code))
        except DomainException as exc:
            await msg.respond(self._error_response(exc.message, 400, exc.code))
        except ValidationError:
            await msg.respond(self._error_response("Request validation failed", 422, "VALIDATION_ERROR"))
        except Exception as exc:
            await msg.respond(self._error_response(str(exc), 500, "INTERNAL_ERROR"))

    @staticmethod
    def _result_to_jsonable(value: Any) -> Any:
        """Convert handler return value to JSON-serializable data."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            return model_dump(mode="json")
        if isinstance(value, dict):
            return {k: RpcMessageHandler._result_to_jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [RpcMessageHandler._result_to_jsonable(v) for v in value]
        return str(value)

    async def _dispatch(self, *, action: str | None, payload: dict[str, Any]) -> Any:
        if action is None or action == "":
            raise DomainException("Missing or empty 'action' field", "MISSING_ACTION")

        if action == "health_check":
            result = await self._health_service.check()
            await self._logger.info(
                "NATS dispatch completed",
                extra={"component": "message_handler", "action": action, "result": result},
            )
            return result

        # async with SqlAlchemyUnitOfWork(db=self._db) as uow:
        #     from app.core.di.app_container import container as di_container

        #     event_service = di_container.event_service(uow=uow)
        #     event_type_service = di_container.event_type_service(uow=uow)
        #     event_type_preferences_service: EventTypePreferencesService = di_container.event_type_preferences_service(
        #         uow=uow
        #     )
        #     message_template_service = di_container.message_template_service(uow=uow)

        #     if action == "list_events":
        #         list_events_query = ListEventsQuery.model_validate(payload)
        #         list_events_cmd = ListEventsCommand(**list_events_query.model_dump())
        #         list_events_items, list_events_total = await event_service.list_events(list_events_cmd)
        #         return ListEventsOutDto(
        #             items=[Event.from_domain(item) for item in list_events_items],
        #             total=list_events_total,
        #         )

        raise DomainException(f"Unknown action: {action}", "UNKNOWN_ACTION")

    def _error_response(self, message: str, status_code: int, code: str | None) -> bytes:
        return json.dumps(
            {
                "ok": False,
                "error": {
                    "status_code": status_code,
                    "code": code or "DOMAIN_ERROR",
                    "message": message,
                },
            },
            default=str,
        ).encode()

"""Dependency injection container."""

from dependency_injector import containers, providers

from app.application.services.health_service import HealthService
from app.core.config.database import DatabaseSettings
from app.core.config.nats import NATSSettings
from app.core.logging import setup_async_logging
from app.infrastructure.messaging.be_data_rpc_client import BeDataRpcClient
from app.infrastructure.messaging.nats_rpc_server import NatsRpcServer
from app.infrastructure.messaging.rpc_message_handler import RpcMessageHandler
from app.infrastructure.persistence.database import DatabaseManager


class Container(containers.DeclarativeContainer):
    """Application DI container."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.interfaces.api.routes.health",
            "app.interfaces.api.routes.base",
            "app.app",
        ],
    )

    config = providers.Configuration()

    # Core infrastructure
    db_settings = providers.Singleton(DatabaseSettings)

    db = providers.Singleton(DatabaseManager, db_settings=db_settings)

    logger = providers.Singleton(setup_async_logging)

    # NATS settings
    nats_settings = providers.Singleton(NATSSettings)

    # Services (defined early to pass to message handlers if needed)
    health_service = providers.Factory(
        HealthService,
        db=db,
    )

    # BE Data RPC Client
    be_data_rpc_client = providers.Singleton(
        BeDataRpcClient,
        settings=nats_settings,
        logger=logger,
    )

    # RPC Message handler
    rpc_message_handler = providers.Factory(
        RpcMessageHandler,
        logger=logger,
        health_service=health_service,
        db=db,
    )

    # NATS RPC server
    nats_rpc_server = providers.Singleton(
        NatsRpcServer,
        settings=nats_settings,
        logger=logger,
        message_handler=rpc_message_handler,
    )

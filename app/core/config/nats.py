"""NATS settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NATSSettings(BaseSettings):
    """Settings for NATS connection."""

    model_config = SettingsConfigDict(env_prefix="NATS_", case_sensitive=False)

    hosts: str = Field(
        "nats://localhost:4222",
        description="URL для подключения к серверам NATS",
    )
    subject: str = Field(
        "bf.>",
        description="Базовый subject для подписки",
    )
    consumer_durable: str = Field(
        "bf-service-consumer",
        description="Имя durable consumer для JetStream",
    )
    consumer_ack_wait: int = Field(
        7200,  # 2 hours
        description="Время ожидания подтверждения (ack) в секундах",
    )
    consumer_max_deliver: int = Field(
        4,
        description="Максимальное количество попыток доставки сообщения",
    )
    fetch_batch_size: int = Field(
        10,
        description="Количество сообщений для выборки за один раз (batch size)",
    )

    # JetStream stream settings
    stream_name: str = Field(
        "bf",
        description="Имя JetStream потока (stream)",
    )
    stream_max_age: int = Field(
        86400,  # 24 hours
        description="Максимальное время хранения сообщений в потоке (в секундах)",
    )
    stream_max_bytes: int = Field(
        1073741824,  # 1GB
        description="Максимальный размер потока в байтах",
    )
    stream_max_messages: int = Field(
        -1,
        description="Максимальное количество сообщений в потоке (-1 для неограниченного)",
    )
    stream_storage_type: str = Field(
        "file",
        description="Тип хранилища потока (file или memory)",
    )

    # RPC Client settings for BE-data
    be_data_rpc_subject: str = Field(
        "be_data.rpc.>",
        description="Subject для RPC-запросов к сервису be-data",
    )
    be_data_rpc_timeout_sec: float = Field(
        10.0,
        description="Таймаут (в секундах) для RPC-запросов к сервису be-data",
    )

    # RPC Server settings
    rpc_subject: str = Field(
        "bf.rpc.bf-service",
        description="Subject для входящих RPC-запросов к нашему сервису",
    )
    rpc_queue: str | None = Field(
        None,
        description="Группа балансировки (queue group) для RPC-запросов",
    )

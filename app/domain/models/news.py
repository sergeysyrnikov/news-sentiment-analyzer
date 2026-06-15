from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SentimentLabel(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class NewsItem:
    id: int
    title: str
    text: str
    source_url: str
    published_at: datetime
    company: str | None = None
    location: str | None = None
    industry: str | None = None


@dataclass
class Cluster:
    id: str
    company: str
    location: str
    industry: str
    news_ids: list[int]
    count: int


@dataclass
class SentimentResult:
    news_id: int
    score: float
    label: SentimentLabel

from datetime import datetime

from app.application.services.clustering_service import _normalize_company, cluster_news
from app.domain.models.news import NewsItem


def test_normalize_company():
    assert _normalize_company("ООО Ромашка") == "ромашка"
    assert _normalize_company("ПАО «Сбербанк»") == "сбербанк"
    assert _normalize_company("ГМК Норильский никель") == "норильский никель"
    assert _normalize_company("АО 'Газпром'") == "газпром"
    assert _normalize_company(None) == ""
    assert _normalize_company("") == ""


def test_clustering_exact_match():
    dt = datetime.now()
    items = [
        NewsItem(
            id=1,
            title="1",
            text="text",
            source_url="url",
            published_at=dt,
            company="Сбербанк",
            location="Москва",
            industry="Финансы",
        ),
        NewsItem(
            id=2,
            title="2",
            text="text",
            source_url="url",
            published_at=dt,
            company="ПАО Сбербанк",
            location="Москва",
            industry="Финансы",
        ),
    ]
    clusters = cluster_news(items)
    assert len(clusters) == 1
    assert clusters[0].count == 2
    assert set(clusters[0].news_ids) == {1, 2}


def test_clustering_different_companies():
    dt = datetime.now()
    items = [
        NewsItem(
            id=1,
            title="1",
            text="text",
            source_url="url",
            published_at=dt,
            company="Сбербанк",
            location="Москва",
            industry="Финансы",
        ),
        NewsItem(
            id=2,
            title="2",
            text="text",
            source_url="url",
            published_at=dt,
            company="Газпром",
            location="Москва",
            industry="Финансы",
        ),
    ]
    clusters = cluster_news(items)
    assert len(clusters) == 2


def test_clustering_fuzzy_match():
    dt = datetime.now()
    items = [
        NewsItem(
            id=1,
            title="1",
            text="text",
            source_url="url",
            published_at=dt,
            company="Яндекс",
            location="Москва",
            industry="IT",
        ),
        NewsItem(
            id=2,
            title="2",
            text="text",
            source_url="url",
            published_at=dt,
            company="Yandex",
            location="Москва",
            industry="IT",
        ),
    ]
    clusters = cluster_news(items)
    assert len(clusters) == 2
    # rapidfuzz может не дать высокий score на разных языках — Яндекс и Yandex в разных кластерах.
    # Давайте добавим похожие на русском: Тинькофф и Т-Банк - тоже разные.
    # Ромашка и Рамашка
    items_fuzzy = [
        NewsItem(
            id=3,
            title="3",
            text="text",
            source_url="url",
            published_at=dt,
            company="Ромашка",
            location="Москва",
            industry="IT",
        ),
        NewsItem(
            id=4,
            title="4",
            text="text",
            source_url="url",
            published_at=dt,
            company="Рамашка",
            location="Москва",
            industry="IT",
        ),
    ]
    clusters_fuzzy = cluster_news(items_fuzzy)
    assert len(clusters_fuzzy) == 1
    assert clusters_fuzzy[0].count == 2


def test_clustering_different_location():
    dt = datetime.now()
    items = [
        NewsItem(
            id=1,
            title="1",
            text="text",
            source_url="url",
            published_at=dt,
            company="Магнит",
            location="Москва",
            industry="Ритейл",
        ),
        NewsItem(
            id=2,
            title="2",
            text="text",
            source_url="url",
            published_at=dt,
            company="Магнит",
            location="Краснодар",
            industry="Ритейл",
        ),
    ]
    clusters = cluster_news(items)
    assert len(clusters) == 2


def test_clustering_empty_fields():
    dt = datetime.now()
    items = [
        NewsItem(
            id=1,
            title="1",
            text="text",
            source_url="url",
            published_at=dt,
            company=None,
            location="Москва",
            industry="",
        ),
        NewsItem(
            id=2,
            title="2",
            text="text",
            source_url="url",
            published_at=dt,
            company="",
            location="Москва",
            industry=None,
        ),
    ]
    clusters = cluster_news(items)
    assert len(clusters) == 1
    assert clusters[0].count == 2

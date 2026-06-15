from datetime import datetime

from app.application.services.sentiment_service import analyze_sentiment, rank_by_sentiment
from app.domain.models.news import NewsItem, SentimentLabel


def create_item(id: int, title: str, text: str) -> NewsItem:
    return NewsItem(id=id, title=title, text=text, source_url="http://test.com", published_at=datetime.now())


def test_analyze_sentiment_positive():
    item = create_item(
        1,
        "Рекордная прибыль",
        "Компания показала значительный рост и рекордную прибыль в этом году. Рынок приветствует это.",
    )
    result = analyze_sentiment(item)
    assert result.label == SentimentLabel.POSITIVE
    assert result.score > 0.0


def test_analyze_sentiment_negative():
    item = create_item(
        2, "Акции упали", "Акции компании потеряли в цене из-за новых санкций. Это вызывает раздражение."
    )
    result = analyze_sentiment(item)
    assert result.label == SentimentLabel.NEGATIVE
    assert result.score < 0.0


def test_analyze_sentiment_neutral():
    item = create_item(
        3, "Обычная новость", "Сегодня компания провела плановое совещание. Никаких важных решений не принято."
    )
    result = analyze_sentiment(item)
    assert result.label == SentimentLabel.NEUTRAL
    assert result.score == 0.0


def test_analyze_sentiment_mixed():
    # Рост/рекордный (позитив) vs упали/потеряли (негатив): «рост» встречается дважды → score 0.2
    item = create_item(4, "Рост продаж, но акции упали", "Несмотря на рекордный рост продаж, акции потеряли в цене.")
    result = analyze_sentiment(item)
    assert result.score == 0.2
    assert result.label == SentimentLabel.POSITIVE


def test_rank_by_sentiment():
    items = [
        create_item(1, "Ужасно упали", "Сбой и штраф"),  # Score -1.0
        create_item(2, "Обычный день", "Кошка перешла дорогу"),  # Score 0.0
        create_item(3, "Рекордный рост", "Прибыль и восторг"),  # Score +1.0
    ]
    ranked = rank_by_sentiment(items)

    assert len(ranked) == 3
    # 3 (most positive) -> 2 -> 1 (most negative)
    assert ranked[0][0].id == 3
    assert ranked[-1][0].id == 1

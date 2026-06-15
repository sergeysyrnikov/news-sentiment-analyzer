import re

from app.domain.models.news import NewsItem, SentimentLabel, SentimentResult

# Вариант A: Словарный подход (быстро, без внешних ML-зависимостей, подходит для MVP/PoC)
# В полноценном продакшене здесь мог бы использоваться transformers с rubert-base-cased-sentiment.

POSITIVE_WORDS = {
    "рекорд",
    "прибыл",
    "рост",
    "позитив",
    "выгодн",
    "гладк",
    "приветству",
    "увеличени",
    "стабильн",
    "восторг",
    "ускорит",
    "создаст",
}

NEGATIVE_WORDS = {
    "упали",
    "потерял",
    "сокращени",
    "сбой",
    "раздражени",
    "отложит",
    "перенос",
    "разочаров",
    "штраф",
    "нарушени",
    "негативн",
    "обеспокоен",
    "санкци",
    "проблем",
}


def analyze_sentiment(item: NewsItem) -> SentimentResult:
    """
    Анализирует тональность новости (title + text) с использованием словарного подхода.
    Возвращает SentimentResult с оценкой от -1.0 до 1.0 и меткой (negative, neutral, positive).
    """
    text_to_analyze = f"{item.title} {item.text}".lower()

    # Разбиваем на слова
    words = re.findall(r"\b\w+\b", text_to_analyze)

    pos_count = 0
    neg_count = 0

    for word in words:
        if any(word.startswith(pw) for pw in POSITIVE_WORDS):
            pos_count += 1
        if any(word.startswith(nw) for nw in NEGATIVE_WORDS):
            neg_count += 1

    total = pos_count + neg_count

    if total == 0:
        score = 0.0
    else:
        # Нормализуем от -1.0 до 1.0
        score = (pos_count - neg_count) / total

    if score > 0.1:
        label = SentimentLabel.POSITIVE
    elif score < -0.1:
        label = SentimentLabel.NEGATIVE
    else:
        label = SentimentLabel.NEUTRAL

    return SentimentResult(news_id=item.id, score=round(score, 2), label=label)


def rank_by_sentiment(items: list[NewsItem]) -> list[tuple[NewsItem, SentimentResult]]:
    """
    Ранжирует список новостей по их сентимент-оценке (по убыванию: от самых позитивных к негативным).
    """
    analyzed = []
    for item in items:
        result = analyze_sentiment(item)
        analyzed.append((item, result))

    # Сортируем по убыванию score
    return sorted(analyzed, key=lambda x: x[1].score, reverse=True)

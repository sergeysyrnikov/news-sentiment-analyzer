import json
import os
from datetime import datetime

from app.application.services.clustering_service import cluster_news
from app.application.services.sentiment_service import rank_by_sentiment
from app.domain.models.news import NewsItem


def load_news(filepath: str) -> list[NewsItem]:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = []
    for row in data:
        items.append(
            NewsItem(
                id=row["id"],
                title=row["title"],
                text=row["text"],
                source_url=row["source_url"],
                published_at=datetime.fromisoformat(row["published_at"].replace("Z", "+00:00")),
                company=row.get("company"),
                location=row.get("location"),
                industry=row.get("industry"),
            )
        )
    return items


def main() -> None:
    filepath = os.path.join(os.path.dirname(__file__), "../../../data/sample_news.json")
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден.")
        return

    print("=== Загрузка данных ===")
    items = load_news(filepath)
    print(f"Загружено новостей: {len(items)}\n")

    print("=== Кластеризация новостей ===")
    clusters = cluster_news(items)
    for c in clusters:
        print(f"Кластер [{c.id[:8]}]:")
        print(f"  Компания:  {c.company or '<не указано>'}")
        print(f"  Локация:   {c.location or '<не указано>'}")
        print(f"  Индустрия: {c.industry or '<не указано>'}")
        print(f"  Новостей:  {c.count} (IDs: {c.news_ids})")
        print("-" * 30)

    print("\n=== Анализ тональности ===")
    ranked = rank_by_sentiment(items)

    print("Топ-3 позитивных новостей:")
    for item, result in ranked[:3]:
        print(f"  [{result.score:>5.2f} | {result.label.value}] {item.title}")

    print("\nТоп-3 негативных новостей:")
    # Негативные в конце списка, так как сортировка по убыванию score
    for item, result in ranked[-3:]:
        print(f"  [{result.score:>5.2f} | {result.label.value}] {item.title}")


if __name__ == "__main__":
    main()

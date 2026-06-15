import hashlib
import re
from typing import Any

from rapidfuzz import fuzz

from app.domain.models.news import Cluster, NewsItem


def _normalize_company(name: str | None) -> str:
    if not name:
        return ""
    # Приводим к нижнему регистру
    norm = name.lower()
    # Убираем кавычки
    norm = re.sub(r"[\'\"«»]", "", norm)
    # Убираем организационно-правовые формы
    forms = [r"\bооо\b", r"\bпао\b", r"\bао\b", r"\bзао\b", r"\bгмк\b"]
    for form in forms:
        norm = re.sub(form, "", norm)
    # Убираем лишние пробелы
    return norm.strip()


def _get_cluster_key(norm_company: str, location: str, industry: str) -> str:
    """Создает уникальный хеш для ключа кластера на основе нормализованных данных."""
    key_str = f"{norm_company}|{location.lower()}|{industry.lower()}"
    return hashlib.md5(key_str.encode("utf-8")).hexdigest()


def cluster_news(items: list[NewsItem]) -> list[Cluster]:
    """
    Кластеризирует новости по компании, локации и индустрии.
    Использует нечеткое сравнение (fuzzy match) для объединения похожих названий компаний.
    """
    clusters_map: dict[str, dict[str, Any]] = {}

    for item in items:
        # Извлекаем данные (в реальном проекте тут был бы NER, если поля пустые)
        company = item.company or ""
        location = item.location or ""
        industry = item.industry or ""

        norm_company = _normalize_company(company)

        matched_key = None

        # Пытаемся найти существующий кластер с похожим именем компании
        for key, cluster_data in clusters_map.items():
            if (
                cluster_data["location"].lower() != location.lower()
                or cluster_data["industry"].lower() != industry.lower()
            ):
                continue

            existing_company = cluster_data["norm_company"]

            # Если точное совпадение или пустое имя (одна локация/индустрия)
            if existing_company == norm_company:
                matched_key = key
                break

            # Нечеткое сравнение
            if norm_company and existing_company:
                score = fuzz.token_sort_ratio(existing_company, norm_company)
                if score >= 85:
                    matched_key = key
                    break

        if matched_key:
            clusters_map[matched_key]["news_ids"].append(item.id)
        else:
            # Создаем новый кластер
            new_key = _get_cluster_key(norm_company, location, industry)
            clusters_map[new_key] = {
                "norm_company": norm_company,
                "company": company,  # сохраняем оригинальное для отображения
                "location": location,
                "industry": industry,
                "news_ids": [item.id],
            }

    # Формируем итоговый список объектов Cluster
    result: list[Cluster] = []
    for key, data in clusters_map.items():
        result.append(
            Cluster(
                id=key,
                company=data["company"],
                location=data["location"],
                industry=data["industry"],
                news_ids=data["news_ids"],
                count=len(data["news_ids"]),
            )
        )

    return result

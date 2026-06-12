# -*- coding: utf-8 -*-
"""Общая логика экспорта данных для веб-сайта."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data import CATEGORIES, DISCLAIMER, STACK_LEVELS, SUBSTANCES  # noqa: E402

TEXT_REPLACEMENTS = {
    "<b>Форма:</b>": "<b>Как используют:</b>",
    "<b>Мин. справочно:</b>": "<b>С чего обычно начинают:</b>",
    "<b>Справочно:</b>": "<b>По заметкам/практике:</b>",
    "<b>Побочки:</b>": "<b>Что может пойти не так:</b>",
    "<b>Статус:</b>": "<b>Где сейчас по статусу:</b>",
    "<b>Эффекты:</b>": "<b>Что обычно ждут:</b>",
    "<b>Стаки:</b>": "<b>С чем дружит:</b>",
    "<b>Логика:</b>": "<b>Почему это вместе имеет смысл:</b>",
    "<b>Применение:</b>": "<b>Как принимают:</b>",
    "<b>Концентрации:</b>": "<b>По концентрациям:</b>",
    "<b>Риск:</b>": "<b>Главный риск:</b>",
    "<b>Риски:</b>": "<b>Главные риски:</b>",
    "<b>Дозы:</b>": "<b>По дозам:</b>",
    "⚠️ Не медицинская рекомендация.": "Не назначение. Просто моя заметка, чтобы быстро сориентироваться.",
    "⚠️ Research only, не медицинская рекомендация.": "Research only. Просто заметка, не инструкция к применению.",
    "⚠️ Research/cosmetic only, не медицинская рекомендация.": "Research/cosmetic only. Просто заметка, не инструкция к применению.",
}


def humanize_text(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def normalize_query(q: str) -> str:
    return q.lower().replace("ё", "е").strip()


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").replace("\n", " ")


def substance_search_text(substance: dict) -> str:
    parts = [
        substance.get("name", ""),
        " ".join(substance.get("tags", [])),
    ]
    if card := substance.get("card"):
        parts.append(strip_html(card))
    for form in (substance.get("forms") or {}).values():
        parts.append(form.get("title", ""))
        parts.append(strip_html(form.get("card", "")))
    return normalize_query(" ".join(parts))


def prepare_substance(sid: str, raw: dict) -> dict:
    item = {
        "id": sid,
        "name": raw.get("name", sid),
        "tags": raw.get("tags", []),
        "components": raw.get("components", []),
    }
    if "card" in raw:
        item["card"] = humanize_text(raw["card"])
    if forms := raw.get("forms"):
        item["forms"] = {
            fid: {
                "title": f["title"],
                "card": humanize_text(f["card"]),
            }
            for fid, f in forms.items()
        }
    return item


def build_payload() -> dict:
    substances = {
        sid: prepare_substance(sid, raw) for sid, raw in SUBSTANCES.items()
    }
    return {
        "categories": CATEGORIES,
        "stackLevels": STACK_LEVELS,
        "substances": substances,
        "disclaimer": humanize_text(DISCLAIMER),
        "meta": {
            "substanceCount": len(substances),
            "categoryCount": len(CATEGORIES),
        },
    }


def search_substance_ids(query: str, limit: int = 30) -> list[str]:
    q = normalize_query(query)
    if not q:
        return []

    matches: list[str] = []
    for sid, raw in SUBSTANCES.items():
        if q in substance_search_text(raw):
            matches.append(sid)
        if len(matches) >= limit:
            break
    return matches

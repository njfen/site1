# -*- coding: utf-8 -*-
"""
Экспорт data.py в data.json для статического хостинга (Cloudflare Pages, GitHub Pages).

Запуск из папки peptide_bot:
  python web/export_static.py
"""

from __future__ import annotations

import json
from pathlib import Path

from data_utils import build_payload

OUT = Path(__file__).resolve().parent / "static" / "data.json"


def main() -> None:
    payload = build_payload()
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=None),
        encoding="utf-8",
    )
    print(f"OK -> {OUT}")
    print(f"   {payload['meta']['substanceCount']} substances, {payload['meta']['categoryCount']} categories")


if __name__ == "__main__":
    main()

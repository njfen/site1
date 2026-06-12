# -*- coding: utf-8 -*-
"""
Peptide Guide Web — сайт на той же базе, что и Telegram-бот.

Локально:
  python web/server.py

Публичный доступ — см. web/DEPLOY.md
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request, send_from_directory

from data_utils import build_payload, search_substance_ids

PAYLOAD = build_payload()

app = Flask(__name__, static_folder="static", static_url_path="")


@app.get("/api/data")
def api_data():
    return jsonify(PAYLOAD)


@app.get("/api/search")
def api_search():
    q = request.args.get("q", "")
    ids = search_substance_ids(q)
    return jsonify([PAYLOAD["substances"][sid] for sid in ids])


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    return send_from_directory(app.static_folder, path)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "1") == "1"

    print(f"Peptide Guide Web -> http://{host}:{port}")
    if host == "0.0.0.0":
        print("   Доступ с других устройств в Wi-Fi: http://<IP-твоего-ПК>:" + str(port))

    app.run(host=host, port=port, debug=debug)

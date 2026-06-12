# Peptide Guide — публикация сайта в интернет

Чтобы открывать сайт **с телефона, планшета и любой сети** (не только с ПК), нужен публичный адрес. Ниже — три рабочих варианта.

---

## Вариант 1 — Cloudflare Pages (рекомендую)

**Бесплатно, всегда онлайн, быстро, HTTPS из коробки.**

Подходит, если не нужен Python-сервер 24/7 — сайт статический, данные в `data.json`.

### Шаги

1. **Залей проект на GitHub** (папка `peptide_bot` — корень репозитория или подпапка).

2. Зайди на [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.

3. Выбери репозиторий и настрой сборку:

   | Поле | Значение |
   |------|----------|
   | **Build command** | `pip install -r requirements.txt && python web/export_static.py` |
   | **Build output directory** | `web/static` |
   | **Root directory** | `peptide_bot` *(если репо = вся папка mcps, укажи путь до peptide_bot)* |

4. **Deploy**. Через минуту получишь адрес вида `https://peptide-guide.pages.dev`.

5. При изменении `data.py` — закоммить, запушить. Cloudflare пересоберёт сайт сам.

### Обновление контента

```bash
# локально перед пушем (опционально — проверить)
python web/export_static.py
git add web/static/data.json data.py
git commit -m "update content"
git push
```

---

## Вариант 2 — Render.com (Python-сервер)

**Бесплатный тариф**, сайт на Flask. На free tier сервис «засыпает» после простоя — первый заход может грузиться 30–60 сек.

### Шаги

1. Репозиторий на GitHub (как выше).

2. [render.com](https://render.com) → **New** → **Web Service** → подключи репо.

3. Настройки:

   | Поле | Значение |
   |------|----------|
   | **Root Directory** | `peptide_bot` |
   | **Build Command** | `pip install -r requirements.txt && python web/export_static.py` |
   | **Start Command** | `gunicorn --chdir web server:app --bind 0.0.0.0:$PORT` |
   | **Instance type** | Free |

4. **Create Web Service** → адрес вида `https://peptide-guide.onrender.com`.

Файл `render.yaml` в корне `peptide_bot` уже есть — Render может подхватить настройки автоматически.

---

## Вариант 3 — только домашний Wi‑Fi (без интернета)

Если нужен доступ **только с телефона в той же Wi‑Fi-сети**, что и ПК:

```powershell
cd peptide_bot
$env:HOST="0.0.0.0"
$env:PORT="5000"
python web/server.py
```

Узнай IP компьютера:

```powershell
ipconfig
# смотри IPv4, например 192.168.1.42
```

На телефоне открой: `http://192.168.1.42:5000`

> ПК должен быть включён, сервер запущен, файрвол Windows может спросить разрешение — нажми «Разрешить».

---

## Бонус — Cloudflare Tunnel (свой ПК, но адрес в интернете)

Если хочешь крутить сервер дома, но иметь **публичный HTTPS-URL** без проброса портов:

1. Установи [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).
2. Запусти сайт локально: `python web/server.py`
3. В другом терминале:

```powershell
cloudflared tunnel --url http://127.0.0.1:5000
```

Выдаст временный URL вида `https://xxx.trycloudflare.com` — работает из любой сети, пока ПК включён.

---

## Сравнение

| Способ | Откуда открыть | Цена | ПК должен работать |
|--------|----------------|------|-------------------|
| Cloudflare Pages | Везде | Бесплатно | Нет |
| Render | Везде | Бесплатно* | Нет |
| Wi‑Fi (0.0.0.0) | Только домашняя сеть | Бесплатно | Да |
| Cloudflare Tunnel | Везде | Бесплатно | Да |

\* Free tier Render засыпает при простое.

---

## Свой домен (опционально)

В Cloudflare Pages или Render: **Custom Domain** → добавь домен → пропиши DNS по инструкции сервиса.

---

## Безопасность

Сайт **публичный** — любой с URL увидит твои заметки. Если контент только для себя:

- не пости ссылку публично;
- или повесь Basic Auth / Cloudflare Access на домен.

Токен Telegram-бота (`BOT_TOKEN`) на сайт **не попадает** — в репозиторий не коммить `.env`.

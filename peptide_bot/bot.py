# -*- coding: utf-8 -*-
"""
Peptide Guide Bot — личная база по пептидам и препаратам.

Навигация на inline-кнопках:
  Главное меню -> категории (похудение/кожа/волосы/ноотропы) -> вещество -> карточка.
  У Semax/Selank между веществом и карточкой есть выбор формы (инъекции/спрей).
  Плюс: список A–Z, поиск по названию/тегам, избранное, дисклеймер.

Запуск:
  1) pip install -r requirements.txt
  2) задать токен в .env (BOT_TOKEN=...) или переменной окружения
  3) python bot.py
"""

import asyncio
import logging
import os

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Conflict, NetworkError, TimedOut
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from data import CATEGORIES, SUBSTANCES, DISCLAIMER, STACK_LEVELS

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Избранное в памяти процесса: {user_id: set(substance_id)}.
# Для продакшена замени на БД (sqlite/redis) — структура совместима.
FAVORITES: dict[int, set] = {}
PAGE_SIZE = 10

WELCOME = (
    "Дарова. Это моя личная база по пептидам, препам и ноотропам.\n\n"
    "Тут всё разложено по целям: похудение, кожа, волосы, восстановление, мозг, связки и всякие интересные research-штуки.\n\n"
    "Можно просто выбрать раздел ниже или написать название вещества в чат."
)


# ----------------------- Клавиатуры -----------------------

def page_slice(items: list, page: int) -> tuple[list, int, int]:
    """Возвращает элементы текущей страницы и границы пагинации."""
    total_pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    return items[start:start + PAGE_SIZE], page, total_pages


def parse_page(value: str | None, default: int = 0) -> int:
    try:
        return max(0, int(value)) if value is not None else default
    except ValueError:
        return default


def home_button() -> InlineKeyboardButton:
    return InlineKeyboardButton("🏠 Меню", callback_data="home")


def back_button(callback_data: str = "home") -> InlineKeyboardButton:
    return InlineKeyboardButton("◀️ Назад", callback_data=callback_data)


def paginated_nav(prefix: str, page: int, total_pages: int) -> list[InlineKeyboardButton]:
    """Кнопки назад/вперёд для длинных списков."""
    row = []
    if page > 0:
        row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}:{page - 1}"))
    row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        row.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"{prefix}:{page + 1}"))
    return row

def main_menu_kb() -> InlineKeyboardMarkup:
    rows = []
    cat_ids = list(CATEGORIES.keys())
    # категории по 2 в ряд
    for i in range(0, len(cat_ids), 2):
        row = [
            InlineKeyboardButton(CATEGORIES[c]["title"], callback_data=f"cat:{c}")
            for c in cat_ids[i:i + 2]
        ]
        rows.append(row)
    rows.append([InlineKeyboardButton("📋 Все вещества A–Z", callback_data="all:0")])
    rows.append([
        InlineKeyboardButton("⭐ Избранное", callback_data="favs"),
        InlineKeyboardButton("ℹ️ О боте", callback_data="about"),
    ])
    return InlineKeyboardMarkup(rows)


def sub_cb(sid: str, origin: str | None = None) -> str:
    """callback_data для открытия карточки вещества с запоминанием «откуда пришёл»."""
    return f"sub:{sid}|{origin}" if origin else f"sub:{sid}"


def category_kb(cat_id: str, page: int = 0) -> InlineKeyboardMarkup:
    rows = []
    items, page, total_pages = page_slice(CATEGORIES[cat_id]["items"], page)
    origin = f"cat:{cat_id}:{page}"
    for sid in items:
        rows.append([
            InlineKeyboardButton(SUBSTANCES[sid]["name"], callback_data=sub_cb(sid, origin))
        ])
    if total_pages > 1:
        rows.append(paginated_nav(f"cat:{cat_id}", page, total_pages))
    rows.append([home_button()])
    return InlineKeyboardMarkup(rows)


def stack_levels_kb() -> InlineKeyboardMarkup:
    """Хаб ноотропных связок: кнопки выбора уровня."""
    rows = [
        [InlineKeyboardButton(level["title"], callback_data=f"lvl:{key}")]
        for key, level in STACK_LEVELS.items()
    ]
    rows.append([home_button()])
    return InlineKeyboardMarkup(rows)


def stack_level_kb(level_key: str) -> InlineKeyboardMarkup:
    """Список связок внутри уровня. Назад — к выбору уровня."""
    origin = f"lvl:{level_key}"
    rows = [
        [InlineKeyboardButton(SUBSTANCES[sid]["name"], callback_data=sub_cb(sid, origin))]
        for sid in STACK_LEVELS[level_key]["items"]
    ]
    rows.append([
        back_button("cat:nootropic_stacks"),
        home_button(),
    ])
    return InlineKeyboardMarkup(rows)


def forms_kb(sid: str, back: str, origin: str | None = None) -> InlineKeyboardMarkup:
    """Кнопки форм выпуска (инъекции/спрей). back — куда вернёт 'Назад'."""
    rows = []
    for form_id, form in SUBSTANCES[sid]["forms"].items():
        cb = f"form:{sid}:{form_id}"
        if origin:
            cb = f"{cb}|{origin}"
        rows.append([InlineKeyboardButton(form["title"], callback_data=cb)])
    rows.append([
        back_button(back),
        home_button(),
    ])
    return InlineKeyboardMarkup(rows)


def card_kb(sid: str, user_id: int, back: str) -> InlineKeyboardMarkup:
    """Кнопки под карточкой вещества. back — callback_data кнопки 'Назад'.

    Если у вещества есть components (связка/стек) — добавляем кнопки на
    карточку каждого компонента. Компонент запоминает текущую карточку как origin.
    """
    fav = sid in FAVORITES.get(user_id, set())
    fav_label = "★ В избранном" if fav else "⭐ В избранное"
    rows = []
    for comp in SUBSTANCES[sid].get("components", []):
        rows.append([
            InlineKeyboardButton(
                f"➡️ {SUBSTANCES[comp]['name']}", callback_data=sub_cb(comp, f"sub:{sid}")
            )
        ])
    fav_cb = f"fav:{sid}|{back}" if back else f"fav:{sid}"
    rows.append([InlineKeyboardButton(fav_label, callback_data=fav_cb)])
    rows.append([
        back_button(back),
        home_button(),
    ])
    return InlineKeyboardMarkup(rows)


def all_substances_kb(page: int = 0) -> InlineKeyboardMarkup:
    rows = []
    items = sorted(SUBSTANCES.items(), key=lambda kv: kv[1]["name"].lower())
    page_items, page, total_pages = page_slice(items, page)
    origin = f"all:{page}"
    for sid, s in page_items:
        rows.append([InlineKeyboardButton(s["name"], callback_data=sub_cb(sid, origin))])
    if total_pages > 1:
        rows.append(paginated_nav("all", page, total_pages))
    rows.append([home_button()])
    return InlineKeyboardMarkup(rows)


# ----------------------- Хелперы рендера -----------------------

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
    "<b>Важно:</b>": "<b>Важно:</b>",
    "<b>Жёстко важно:</b>": "<b>Очень важно:</b>",
    "⚠️ Не медицинская рекомендация.": "Не назначение. Просто моя заметка, чтобы быстро сориентироваться.",
    "⚠️ Research only, не медицинская рекомендация.": "Research only. Просто заметка, не инструкция к применению.",
    "⚠️ Research/cosmetic only, не медицинская рекомендация.": "Research/cosmetic only. Просто заметка, не инструкция к применению.",
}


def humanize_text(text: str) -> str:
    """Делает карточки менее сухими, не ломая HTML-разметку Telegram."""
    for old, new in TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def normalize_query(text: str) -> str:
    return text.strip().lower().replace("ё", "е")


def substance_search_text(substance: dict) -> str:
    parts = [
        substance.get("name", ""),
        " ".join(substance.get("tags", [])),
        substance.get("card", ""),
    ]
    for form in substance.get("forms", {}).values():
        parts.extend([form.get("title", ""), form.get("card", "")])
    return normalize_query(" ".join(parts))


async def edit_or_send(update: Update, text: str, kb: InlineKeyboardMarkup) -> None:
    """Редактирует сообщение при callback, иначе отправляет новое."""
    text = humanize_text(text)
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=kb, parse_mode=ParseMode.HTML
            )
        except BadRequest as exc:
            # Повторное нажатие той же кнопки — контент не изменился, это не ошибка.
            if "not modified" in str(exc).lower():
                return
            raise
    else:
        await update.effective_message.reply_text(
            text, reply_markup=kb, parse_mode=ParseMode.HTML
        )


def back_target_for(sid: str) -> str:
    """Куда возвращает кнопка 'Назад' с карточки — в категорию вещества."""
    for cat_id, cat in CATEGORIES.items():
        if sid in cat["items"]:
            return f"cat:{cat_id}"
    return "home"


def validate_data() -> None:
    """Проверяет, что все id в меню и связках реально существуют."""
    errors = []

    for cat_id, cat in CATEGORIES.items():
        if "title" not in cat or "items" not in cat:
            errors.append(f"Категория {cat_id}: нужны ключи title и items")
            continue
        for sid in cat["items"]:
            if sid not in SUBSTANCES:
                errors.append(f"Категория {cat_id}: неизвестный id {sid}")

    for sid, substance in SUBSTANCES.items():
        if "name" not in substance:
            errors.append(f"Карточка {sid}: нет name")
        if "card" not in substance and "forms" not in substance:
            errors.append(f"Карточка {sid}: нужен card или forms")
        for comp in substance.get("components", []):
            if comp not in SUBSTANCES:
                errors.append(f"Связка {sid}: неизвестный компонент {comp}")
        for form_id, form in substance.get("forms", {}).items():
            if "title" not in form or "card" not in form:
                errors.append(f"Форма {sid}:{form_id}: нужны title и card")

    for level_key, level in STACK_LEVELS.items():
        for sid in level.get("items", []):
            if sid not in SUBSTANCES:
                errors.append(f"Уровень связок {level_key}: неизвестный id {sid}")

    if errors:
        raise SystemExit("Ошибки в data.py:\n- " + "\n- ".join(errors))


async def show_substance(update: Update, sid: str, origin: str | None = None) -> None:
    """Показ вещества: либо выбор формы, либо сразу карточка.

    origin — callback_data, куда вернёт 'Назад'. Если не задан, берём категорию вещества.
    """
    s = SUBSTANCES[sid]
    user_id = update.effective_user.id
    back = origin or back_target_for(sid)
    if "forms" in s:
        text = (
            f"<b>{s['name']}</b>\n"
            f"{' · '.join('#' + t for t in s.get('tags', []))}\n\n"
            "Выбери форму выпуска:"
        )
        await edit_or_send(update, text, forms_kb(sid, back, origin))
    else:
        await edit_or_send(update, s["card"], card_kb(sid, user_id, back))


# ----------------------- Хендлеры -----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        humanize_text(WELCOME), reply_markup=main_menu_kb(), parse_mode=ParseMode.HTML
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    # origin кодируется через '|' после основной команды: "sub:semax|lvl:strong".
    origin = None
    if "|" in data:
        data, origin = data.split("|", 1)

    if not data.startswith("fav:"):
        await query.answer()

    if data == "noop":
        return

    if data == "home":
        await edit_or_send(update, WELCOME, main_menu_kb())

    elif data == "about":
        kb = InlineKeyboardMarkup([[home_button()]])
        await edit_or_send(update, DISCLAIMER, kb)

    elif data.startswith("all"):
        page = parse_page(data.split(":", 1)[1] if ":" in data else None)
        await edit_or_send(update, "📋 <b>Все вещества</b> (A–Z):", all_substances_kb(page))

    elif data == "favs":
        await show_favorites(update)

    elif data.startswith("lvl:"):
        level_key = data.split(":", 1)[1]
        if level_key not in STACK_LEVELS:
            await edit_or_send(update, "Не нашёл такой уровень. Вернись в меню.", main_menu_kb())
            return
        level = STACK_LEVELS[level_key]
        text = f"<b>{level['title']} связки</b>\n\n{level['desc']}\n\nВыбери связку:"
        await edit_or_send(update, text, stack_level_kb(level_key))

    elif data.startswith("cat:"):
        parts = data.split(":")
        cat_id = parts[1]
        page = parse_page(parts[2] if len(parts) > 2 else None)
        if cat_id not in CATEGORIES:
            await edit_or_send(update, "Не нашёл такой раздел. Вернись в меню.", main_menu_kb())
            return
        cat = CATEGORIES[cat_id]
        # Раздел-хаб (ноотропные связки): показываем выбор уровня, а не список.
        if cat.get("hub") == "stack_levels":
            text = f"<b>{cat['title']}</b>\n\n{cat['desc']}"
            await edit_or_send(update, text, stack_levels_kb())
            return
        text = f"<b>{cat['title']}</b>\n\n{cat['desc']}\n\nВыбери препарат:"
        await edit_or_send(update, text, category_kb(cat_id, page))

    elif data.startswith("sub:"):
        sid = data.split(":", 1)[1]
        if sid not in SUBSTANCES:
            await edit_or_send(update, "Не нашёл такую карточку. Вернись в меню.", main_menu_kb())
            return
        await show_substance(update, sid, origin)

    elif data.startswith("form:"):
        _, sid, form_id = data.split(":", 2)
        if sid not in SUBSTANCES or form_id not in SUBSTANCES[sid].get("forms", {}):
            await edit_or_send(update, "Не нашёл такую форму. Вернись в меню.", main_menu_kb())
            return
        form = SUBSTANCES[sid]["forms"][form_id]
        # назад к выбору формы, сохраняя исходный origin (откуда зашли в вещество)
        back = f"sub:{sid}" + (f"|{origin}" if origin else "")
        await edit_or_send(update, form["card"], card_kb(sid, user_id, back))

    elif data.startswith("fav:"):
        sid = data.split(":", 1)[1]
        if sid not in SUBSTANCES:
            await query.answer("Карточка не найдена")
            return
        await toggle_favorite(update, sid, origin)

    else:
        await edit_or_send(update, "Не понял эту кнопку. Вернись в меню.", main_menu_kb())


async def toggle_favorite(update: Update, sid: str, back: str | None = None) -> None:
    user_id = update.effective_user.id
    favs = FAVORITES.setdefault(user_id, set())
    if sid in favs:
        favs.discard(sid)
        note = "Убрано из избранного"
    else:
        favs.add(sid)
        note = "Добавлено в избранное ⭐"
    await update.callback_query.answer(note)
    # перерисовываем кнопки, сохраняя кнопку 'Назад' (back пришёл из origin)
    await update.callback_query.edit_message_reply_markup(
        reply_markup=card_kb(sid, user_id, back or back_target_for(sid))
    )


async def show_favorites(update: Update) -> None:
    user_id = update.effective_user.id
    favs = {sid for sid in FAVORITES.get(user_id, set()) if sid in SUBSTANCES}
    FAVORITES[user_id] = favs
    if not favs:
        kb = InlineKeyboardMarkup([[home_button()]])
        await edit_or_send(update, "⭐ Избранное пусто.\n\nОткрой карточку и добавь вещество.", kb)
        return
    rows = []
    for sid in sorted(favs, key=lambda x: SUBSTANCES[x]["name"].lower()):
        rows.append([InlineKeyboardButton(SUBSTANCES[sid]["name"], callback_data=sub_cb(sid, "favs"))])
    rows.append([home_button()])
    await edit_or_send(update, "⭐ <b>Избранное</b>:", InlineKeyboardMarkup(rows))


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Поиск по названию и тегам — на любой текст."""
    raw_query = update.message.text.strip()
    q = normalize_query(raw_query)
    matches = []
    for sid, s in SUBSTANCES.items():
        haystack = substance_search_text(s)
        if q in haystack:
            matches.append(sid)

    if not matches:
        await update.message.reply_text(
            f"По запросу «{raw_query}» ничего не нашёл 🤔\n"
            "Попробуй название (напр. «семаглутид», «ghk», «минокс») или открой меню.",
            reply_markup=main_menu_kb(),
        )
        return

    rows = [[InlineKeyboardButton(SUBSTANCES[s]["name"], callback_data=f"sub:{s}")] for s in matches[:20]]
    if len(matches) > 20:
        rows.append([InlineKeyboardButton(f"Показал 20 из {len(matches)}", callback_data="noop")])
    rows.append([home_button()])
    await update.message.reply_text(
        f"🔍 Нашёл по запросу «{raw_query}»:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error

    if isinstance(error, Conflict):
        logger.warning(
            "Conflict: запущена ещё одна копия бота. "
            "Закрой лишние процессы — должен работать только один python bot.py."
        )
        return

    if isinstance(error, (NetworkError, TimedOut)):
        logger.warning("Сетевая проблема: %s. Обычно само восстановится.", error)
        return

    logger.exception("Unhandled bot error", exc_info=error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Что-то пошло не так. Я уже записал ошибку в консоль, можно поправить."
            )
        except Exception:
            pass


def _read_env_file(path: str) -> None:
    """Простой парсер .env без внешних зависимостей (на случай отсутствия dotenv)."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        pass


def main() -> None:
    validate_data()

    # .env ищем рядом с этим файлом, чтобы не зависеть от текущей папки запуска
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    _read_env_file(env_path)

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit(
            "Не задан BOT_TOKEN.\n"
            f"Проверь файл: {env_path}\n"
            "Внутри должна быть строка вида:  BOT_TOKEN=123456789:AA...\n"
            "Либо задай переменную окружения BOT_TOKEN."
        )

    # Python 3.14 больше не создаёт event loop неявно — создаём сами,
    # иначе run_polling падает с "There is no current event loop".
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)

    logger.info("Bot started. Press Ctrl+C to stop.")
    # drop_pending_updates чистит очередь, чтобы старые нажатия не прилетали после рестарта.
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()

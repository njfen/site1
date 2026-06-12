# Peptide Guide Bot

Личная Telegram-база по пептидам и препаратам. Навигация на inline-кнопках:
цели → вещества → карточки. Поиск по названию/тегам, избранное.

## Что внутри

Все пептиды — **инъекционные** (SC/IM). Исключения: ноотропы (есть спреи),
Minoxidil (топик).

- **🔥 Похудение:** Semaglutide, Tirzepatide, Retatrutide, Cagrilintide
- **✨ Кожа:** GHK-Cu, BPC-157, TB-500
- **💇 Волосы:** Minoxidil (топик) + GHK-Cu (синергия)
- **🧠 Ноотропы:** Semax, Selank, Alpha-GPC, CDP-Choline, Uridine, DHA, Caffeine, L-Theanine, Phenylpiracetam/Fonturacetam, Phenylpiracetam Hydrazide, Fasoracetam, Noopept, Methylene Blue, Piracetam, Aniracetam, Oxiracetam, Pramiracetam, Coluracetam, Sunifiram, Adamax, Bromantane/Ладастен, Dihexa, Tropoflavin/Eutropoflavin (7,8-DHF), Cerebrolysin, Mexidol, Meldonium/Милдронат, Huperzine-A, Galantamine, Lecithin, DMAE, Nicergoline, Vinpocetine, Bacopa, Ginseng, Ginkgo, Ashwagandha, Lion's Mane, Rhodiola, L-Tyrosine, Creatine, Phosphatidylserine, Витамины B, Prucalopride, Sabroxy (Ороксилин А), PRL-8-53, Unifiram, Donepezil, P21, PE-22-28, Magnesium Glycinate
- **💊 Стимуляторы:** Modafinil, Adrafinil, Nicotine, Methylphenidate (Rx)
- **🧠💊 Настроение / МАО:** Tesofensine, Selegiline, Rasagiline, Safinamide, Tranylcypromine (Транил), Phenelzine, Rolipram
- **🧩 Ноотропные связки** (хаб с делением на уровни):
  - 🟢 Лёгкие: Clean Focus, Mr Happy, Memory Growth, Calm Social
  - 🟡 Средние: Racetam Base, Deep Work, Stress Drive, Flow & Social, Neurogenesis, Русский щит, Cerebro Recovery
  - 🔴 Сильные: Русский блиц (Фенотропил+Семакс+Alpha-GPC), Limitless, Phenyl Sprint, Cold War, Mito Focus, NeuroGrowth (research), Sunifiram Sprint (research), Adamax+ (research), Modafinil Focus, Modafinil Analytics, IQMax Memory, Unifiram Blitz (research), NeuroPeptide (research)
- **🩹 Восстановление:** BPC-157, TB-500, CJC-1295 + Ipamorelin, Tesamorelin, Sermorelin, Ipamorelin, AOD-9604
- **⚡ Митохондрии / энергия:** MOTS-c, SS-31 / Elamipretide, 5-Amino-1MQ, PQQ, CoQ10, ALCAR, Melatonin
- **🧬 Longevity / иммунка:** Epitalon, Thymosin Alpha-1, KPV, LL-37, DSIP/Дельтаран
- **🦴 Фреймаксинг:** IGF-1 LR3/DES, MGF/PEG-MGF, MK-677/Ибутаморен, GHRP-2/6, Hexarelin, Follistatin-344, ACE-031, Меклозин (FGFR3), Литий (микро), Астрагал, Таурин, Ингибиторы ароматазы, Коллаген+MSM + связки (Frame Stack, Ключичный протокол, ААС-курс — справочно)
- **🧪 Frontier / Будущее:** малоизученные перспективные молекулы без дозировок (SLU-PP-332, GDF-8 Propeptide 2.0, MG53, SCUBE3, Timosense, hCAP-18 fragment, NLX-112, R18, UGN-P1, PNC-27, SGLT2-пептид)
- **🔗 Связки / стеки:** CagriSema, Glow, Wolverine, Hair, Mito, Longevity
- 📋 Список A–Z · 🔍 Поиск · ⭐ Избранное · ℹ️ Дисклеймер

У связок под карточкой — кнопки перехода на каждый компонент.
Карточки выводятся в живом стиле: `как используют`, `с чего обычно начинают`, `с чем дружит`, `что может пойти не так`.
У Frontier-раздела дозировок нет: там только research-заметки.

## Установка

```bash
pip install -r requirements.txt
```

## Токен

1. Открой [@BotFather](https://t.me/BotFather) → `/newbot` → получи токен.
2. Скопируй `.env.example` в `.env` и вставь токен:

```
BOT_TOKEN=123456789:AAA...
```

(или задай переменную окружения `BOT_TOKEN`).

## Запуск бота

```bash
python bot.py
```

Команды бота: `/start`, `/menu`. Любой текст = поиск.

## Веб-сайт

Те же данные из `data.py`, но удобнее: поиск, избранное (localStorage), навигация по разделам, ноотропные связки по уровням, формы Semax/Selank.

```bash
pip install -r requirements.txt
python web/server.py
```

Открой в браузере: **http://127.0.0.1:5000**

### Доступ с других устройств (интернет)

Подробная инструкция: **`web/DEPLOY.md`**

Кратко — лучший бесплатный вариант:

1. Залей `peptide_bot` на GitHub
2. Подключи **Cloudflare Pages** (Build: `python web/export_static.py`, Output: `web/static`)
3. Получишь постоянный URL вида `https://xxx.pages.dev` — открывается с любого устройства

Только домашний Wi‑Fi (без интернета):

```powershell
$env:HOST="0.0.0.0"
python web/server.py
# на телефоне: http://<IP-ПК>:5000
```

Структура:
- `web/server.py` — Flask API (`/api/data`, `/api/search`)
- `web/static/` — фронтенд (HTML/CSS/JS)

При изменении `data.py` перезапусти сервер — данные подтянутся автоматически.

## Где что менять

- `data.py` — все вещества и категории. Добавить препарат: дописать запись в
  `SUBSTANCES` и id в нужную категорию `CATEGORIES`. Для форм выпуска
  (инъекции/спрей) используй ключ `forms` (см. `semax` / `selank`).
  Лучше писать карточки коротко и по-человечески: что это, зачем, старт, связки, риски.
- `bot.py` — логика меню, кнопок, поиска, избранного.

## Что уже есть в коде

- Пагинация длинных разделов и списка A–Z, чтобы Telegram не показывал огромную простыню кнопок.
- Проверка `data.py` при старте: бот сразу скажет, если в категории или связке указан несуществующий id.
- Поиск идёт по названию, тегам и тексту карточки.
- Центральный обработчик ошибок пишет проблему в консоль и отвечает пользователю.

## Заметки

- Избранное хранится в памяти процесса (сбросится при перезапуске).
  Для постоянного хранения замени словарь `FAVORITES` на SQLite/Redis —
  структура `{user_id: set(substance_id)}` совместима.
- Весь контент — личные заметки, **не медицинская рекомендация**.

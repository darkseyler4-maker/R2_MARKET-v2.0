
# ================== R2 BUYER BOT — ALL IN ONE (FULL & FIXED) ==================
# aiogram 3.x | FULL PRODUCTION | SINGLE FILE
# ============================================================================

import asyncio
import time
import logging
import traceback
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ================== CONFIG ==================

import os

# Load configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8353270333:AAGBMlTFT4W4_Z_wBw8f0poJs40nEd75Zgg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6216901670"))
GROUP_ID = os.getenv("GROUP_ID")  # disabled in test mode

DB = os.getenv("DATABASE_PATH", "database.db")

SERVER_RATES = {
    "R2 Rise": {
        "UAH": 65,
        "USDT": 1.4
    }
}

RATE_UAH = SERVER_RATES["R2 Rise"]["UAH"]
RATE_USDT = SERVER_RATES["R2 Rise"]["USDT"]

SERVER_LIMITS = {
    "R2 Rise": {
        "UAH_MIN": 10,
        "USDT_BEP20_MIN": 10,
        "USDT_TRC20_MIN": 50
    }
}

BAN_SECONDS = 15 * 60
TIMER_SECONDS = 10 * 60
SPAM_DELAY = 1.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ================== TEXTS ==================

TEXT = {
    "menu_title": (
        "✨ <b>R2 Silver Trade</b> ✨\n\n"
        "Добро пожаловать в официальный сервис безопасных сделок серебром R2 Online.\n"
        "Все операции сопровождаются администратором — спокойно и надежно."
    ),
    "rate": (
        "💱 <b>Актуальный курс — R2 Rise</b>\n\n"
        "💴 Гривны: <b>{uah} грн</b> за 1кк\n"
        "💵 USDT: <b>{usdt} USDT</b> за 1кк\n\n"
        "Курс может меняться — уточняйте перед подтверждением сделки."
    ),
    "about": (
        "ℹ️ <b>О сервисе</b>\n\n"
        "Этот бот помогает оформить безопасную сделку по продаже серебра в R2 Online.\n\n"
        "🔐 Сделки проходят под контролем администратора.\n"
        "🎮 Передача серебра и оплата происходят только внутри игры — бот не принимает платежи."
    ),
    "deal_sent": (
        "🆕 <b>Заявка отправлена</b>\n\n"
        "Администратор вскоре свяжется с вами и назначит удобное время для сделки.\n\n"
        "Пожалуйста, ожидайте уведомления."
    ),
    "enter_number_error": "⚠️ Пожалуйста, введите корректное числовое значение.",
    "deal_finished": (
        "🎉 <b>Сделка завершена</b>\n\n"
        "Спасибо за то, что воспользовались нашим сервисом."
    ),
    # ---- MARKETPLACE TEXTS ----
    "market_main": (
        "🛒 <b>РЫНОК — Добро пожаловать</b>\n\n"
        "Здесь вы можете просматривать объявления, размещать товары (до 5 активных),\n"
        "управлять лотами и общаться с продавцами.\n\n"
        "Выберите действие:"
    ),
    "market_view_category": (
        "👀 <b>Просмотр товаров</b>\n\n"
        "Выберите категорию:"
    ),
    "market_weapons": (
        "⚔️ <b>Оружие</b>\n\n"
        "Выберите тип оружия:"
    ),
    "market_equipment": (
        "🛡️ <b>Экипировка</b>\n\n"
        "Выберите предмет экипировки:"
    ),
    "market_accessories": (
        "💍 <b>Аксессуары</b>\n\n"
        "Выберите аксессуар:"
    ),
    "market_spheres": (
        "🔮 <b>Сферы</b>\n\n"
        "Выберите сферу:"
    ),
    "market_no_listings": (
        "📭 <b>Объявлений не найдено</b>\n\n"
        "В этой категории пока пусто. Попробуйте позже или добавьте своё предложение."
    ),
    "market_create_main": (
        "➕ <b>Разместить объявление</b>\n\n"
        "<b>Лимит:</b> до 5 активных объявлений.\n\n"
        "Выберите категорию для размещения:"
    ),
    "market_listing_limit": (
        "⚠️ <b>Достигнут лимит объявлений</b>\n\n"
        "У вас уже 5 активных объявлений. Удалите или завершите одно, чтобы создать новое."
    ),
    "market_create_category": (
        "📂 <b>Выберите категорию</b>"
    ),
    "market_enter_price": (
        "💰 <b>Введите цену (в кк)</b>"
    ),
    "market_preview": (
        "👁️ <b>Предпросмотр объявления</b>\n\nПроверьте текст и цену перед публикацией."
    ),
    "market_my_listings": (
        "📦 <b>Мои объявления</b>\n\n"
        "Выберите фильтр:"
    ),
    "market_active": (
        "⏳ <b>Активные объявления</b>"
    ),
    "market_search_prompt": (
        "🔍 <b>Поиск по названию</b>\n\n"
        "Введите название товара или ключевое слово:"
    ),
    "market_search_no_results": (
        "📭 <b>По вашему запросу ничего не найдено</b>\n\n"
        "Попробуйте другое ключевое слово или просмотрите товары по категориям."
    ),
    # completed/rejected listing types removed (menu simplified)
}

# ================== DATABASE ==================

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                banned_until INTEGER DEFAULT 0
            )"""
        )

        await db.execute(
            """CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target TEXT,
                created_at INTEGER
            )"""
        )

        await db.execute(
            """CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                currency TEXT,
                bank TEXT,
                initials TEXT,
                usdt_net TEXT,
                amount_kk INTEGER,
                deal_time TEXT,
                nick TEXT,
                status TEXT,
                created_at INTEGER
            )"""
        )

        # ---- migration: timer_until ----
        cur = await db.execute("PRAGMA table_info(deals)")
        cols = [row[1] for row in await cur.fetchall()]
        if "timer_until" not in cols:
            await db.execute("ALTER TABLE deals ADD COLUMN timer_until INTEGER")

        # ---- migration: usdt_net ----
        cur = await db.execute("PRAGMA table_info(deals)")
        cols = [row[1] for row in await cur.fetchall()]
        if "usdt_net" not in cols:
            await db.execute("ALTER TABLE deals ADD COLUMN usdt_net TEXT")


        # ---- rates table + safe migration ----
        await db.execute(
            """CREATE TABLE IF NOT EXISTS rates (
                server TEXT PRIMARY KEY,
                rate_uah REAL,
                rate_usdt REAL
            )"""
        )

        cur = await db.execute("PRAGMA table_info(rates)")
        cols = [row[1] for row in await cur.fetchall()]

        if "uah_min" not in cols:
            await db.execute("ALTER TABLE rates ADD COLUMN uah_min INTEGER DEFAULT 10")
        if "usdt_bep20_min" not in cols:
            await db.execute("ALTER TABLE rates ADD COLUMN usdt_bep20_min INTEGER DEFAULT 10")
        if "usdt_trc20_min" not in cols:
            await db.execute("ALTER TABLE rates ADD COLUMN usdt_trc20_min INTEGER DEFAULT 50")

        await db.execute(
            """INSERT OR IGNORE INTO rates
            (server, rate_uah, rate_usdt, uah_min, usdt_bep20_min, usdt_trc20_min)
            VALUES (?,?,?,?,?,?)""" ,
            (
                "R2 Rise",
                SERVER_RATES["R2 Rise"]["UAH"],
                SERVER_RATES["R2 Rise"]["USDT"],
                SERVER_LIMITS["R2 Rise"]["UAH_MIN"],
                SERVER_LIMITS["R2 Rise"]["USDT_BEP20_MIN"],
                SERVER_LIMITS["R2 Rise"]["USDT_TRC20_MIN"]
            )
        )

        # ---- MARKETPLACE TABLES ----
        await db.execute(
            """CREATE TABLE IF NOT EXISTS market_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                subcategory TEXT,
                item_name TEXT,
                price INTEGER,
                runes TEXT,
                status TEXT DEFAULT 'active',
                created_at INTEGER,
                seller_username TEXT
            )"""
        )

        # ---- migration: runes column for market_listings ----
        cur = await db.execute("PRAGMA table_info(market_listings)")
        cols = [row[1] for row in await cur.fetchall()]
        if "runes" not in cols:
            await db.execute("ALTER TABLE market_listings ADD COLUMN runes TEXT")

        # ---- migration: enchant column for market_listings ----
        cur = await db.execute("PRAGMA table_info(market_listings)")
        cols = [row[1] for row in await cur.fetchall()]
        if "enchant" not in cols:
            await db.execute("ALTER TABLE market_listings ADD COLUMN enchant INTEGER DEFAULT 0")

        # ---- migration: expires_at column for 24-hour timer ----
        cur = await db.execute("PRAGMA table_info(market_listings)")
        cols = [row[1] for row in await cur.fetchall()]
        if "expires_at" not in cols:
            await db.execute("ALTER TABLE market_listings ADD COLUMN expires_at INTEGER")

        # ---- migration: delete_reason column for tracking deletion reason ----
        cur = await db.execute("PRAGMA table_info(market_listings)")
        cols = [row[1] for row in await cur.fetchall()]
        if "delete_reason" not in cols:
            await db.execute("ALTER TABLE market_listings ADD COLUMN delete_reason TEXT")

        # ---- migration: listing_type column for SELL/BUY indicator ----
        cur = await db.execute("PRAGMA table_info(market_listings)")
        cols = [row[1] for row in await cur.fetchall()]
        if "listing_type" not in cols:
            await db.execute("ALTER TABLE market_listings ADD COLUMN listing_type TEXT DEFAULT 'SELL'")

        await db.execute(
            """CREATE TABLE IF NOT EXISTS market_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                listing_id INTEGER,
                created_at INTEGER,
                UNIQUE(user_id, listing_id)
            )"""
        )

        await db.execute(
            """CREATE TABLE IF NOT EXISTS market_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reviewer_id INTEGER,
                seller_id INTEGER,
                rating INTEGER,
                comment TEXT,
                created_at INTEGER
            )"""
        )

        # ---- listing_slot_penalty table for tracking per-slot 3-hour penalties ----
        await db.execute(
            """CREATE TABLE IF NOT EXISTS listing_slot_penalty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                slot_number INTEGER,
                penalty_until INTEGER,
                reason TEXT,
                UNIQUE(user_id, slot_number)
            )"""
        )

        # ---- listing_creation_penalty table for backward compatibility (deprecated) ----
        await db.execute(
            """CREATE TABLE IF NOT EXISTS listing_creation_penalty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                penalty_until INTEGER,
                reason TEXT
            )"""
        )

        await db.commit()

async def db_exec(sql, params=(), fetch=False, one=False):
    async with aiosqlite.connect(DB) as conn:
        cur = await conn.execute(sql, params)
        await conn.commit()
        if fetch:
            return await (cur.fetchone() if one else cur.fetchall())

async def is_banned(uid):
    r = await db_exec("SELECT banned_until FROM users WHERE user_id=?", (uid,), True, True)
    return r and r[0] > int(time.time())

async def has_active(uid):
    # active only if amount_kk IS NOT NULL and status active
    r = await db_exec(
        "SELECT id FROM deals WHERE user_id=? AND status='in_work'",
        (uid,), True, True
    )
    return bool(r)


async def log_admin(admin_id, action, target):
    await db_exec(
        "INSERT INTO admin_logs (admin_id,action,target,created_at) VALUES (?,?,?,?)",
        (admin_id, action, target, int(time.time()))
    )

# ================== KEYBOARDS ==================

def reply_kb(*texts):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t)] for t in texts],
        resize_keyboard=True
    )

def inline_kb(pairs):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=str(t), callback_data=d)] for t, d in pairs]
    )

# ================== HELPERS ==================

def kk_fmt(k):
    if k is None:
        return "—"
    return f"{k}кк ({k*1_000_000:,}".replace(",", ".") + ")"

def sum_fmt(cur, k):
    return f"{k*RATE_UAH} грн" if cur == "UAH" else f"{k*RATE_USDT:.2f} USDT"

_last_action = {}

# Mapping for rune display (1..5 -> roman numerals)
ROMAN_RUNES = {
    "1": "Ⅰ",
    "2": "Ⅱ",
    "3": "Ⅲ",
    "4": "Ⅳ",
    "5": "Ⅴ",
}

# Color mapping for runes with emoji indicators
RUNE_COLORS = {
    "1": "⚪",  # White
    "2": "🟡",  # Yellow/Gold
    "3": "🟢",  # Green
    "4": "🔵",  # Blue
    "5": "🟣",  # Purple/Magenta
}

def format_runes(runes):
    if not runes:
        return ""
    colored_runes = []
    for r in runes:
        roman = ROMAN_RUNES.get(str(r), str(r))
        color_emoji = RUNE_COLORS.get(str(r), "")
        colored_runes.append(f'{color_emoji} <b>{roman}</b>')
    return ", ".join(colored_runes)


def enchant_marker(enchant):
    """Return a compact icon representation for enchant level.
    - +0 => grey circle
    - 1..10 => repeated diamond markers (capped at 10)
    - >10 => 10 markers + numeric suffix
    """
    # Simplified: show only numeric enchant level (e.g. +5) as bold/stylized text
    if enchant is None:
        return ""
    try:
        lvl = int(enchant)
    except:
        return f" <b>+{enchant}</b>"

    # zero-level is displayed as +0 (explicit)
    return f" <b>+{stylize_enchant_number(lvl)}</b>"


def price_marker(price):
    """Return a compact icon/marker representation for price in kк.
    We display up to 10 coin icons representing price tiers (each icon ~=10kк),
    and keep the numeric price in bold for clarity.
    """
    if price is None:
        return ""
    try:
        p = int(price)
    except:
        return f"<b>{price}кк</b>"

    # Show only numeric price (fullwidth digits)
    return f"<b>{stylize_price_number(p)}кк</b>"


def stylize_number(n):
    """Return a visually heavier/bolder Unicode-stylized representation of digits.
    Uses mathematical bold digits where available to amplify appearance.
    """
    # Map ASCII digits to Mathematical Bold Digits (U+1D7CE..U+1D7D7)
    bold_map = {
        "0": "𝟎",
        "1": "𝟏",
        "2": "𝟐",
        "3": "𝟑",
        "4": "𝟒",
        "5": "𝟓",
        "6": "𝟔",
        "7": "𝟕",
        "8": "𝟖",
        "9": "𝟗",
        "-": "-",
        ",": ",",
        ".": "."
    }
    s = str(n)
    return "".join(bold_map.get(ch, ch) for ch in s)


def stylize_enchant_number(n: int) -> str:
    """Return circled-number glyphs for small integers (0..20).
    Falls back to plain decimal for out-of-range values.
    """
    # Use plain decimal digits — visual bolding is applied via HTML <b> wrappers
    try:
        v = int(n)
    except:
        return str(n)
    return str(v)


def stylize_price_number(n: int) -> str:
    """Return a string with fullwidth digits for better visual weight in prices."""
    # Return plain ASCII digits; bold styling is handled by surrounding <b> tags.
    return str(n)

async def anti_spam(uid):
    now = time.time()
    if uid in _last_action and now - _last_action[uid] < SPAM_DELAY:
        return False
    _last_action[uid] = now
    return True

# ================== FSM ==================

class DealFSM(StatesGroup):
    currency = State()
    bank = State()
    initials = State()
    usdt_net = State()
    amount = State()
    preview = State()
    admin_time = State()
    admin_nick = State()


class AdminRateFSM(StatesGroup):
    choose = State()
    edit_value = State()


# ================== MARKETPLACE FSM ==================

class MarketFSM(StatesGroup):
    view_category = State()
    view_subcategory = State()
    create_listing_type = State()
    create_category = State()
    create_subcategory = State()
    create_weapon_rank = State()
    create_weapon_selection = State()
    create_runes = State()
    create_enchant = State()
    create_price = State()
    create_preview = State()
    edit_price = State()
    my_listings_filter = State()
    search_query = State()

# ================== BOT INIT ==================

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())



# ================== MENU ==================

# ================== MARKETPLACE FUNCTIONS ==================

# ---- CATEGORY STRUCTURE ----
MARKET_CATEGORIES = {
    "⚔️ Оружие": {
        "🗡️ Ближнее": "melee",
        "🏹 Дальнее": "ranged"
    },
    "🛡️ Экипировка": {
        "🪖 Шлем": "helmet",
        "🦺 Доспех": "armor",
        "🧤 Перчатки": "gloves",
        "👢 Сапоги": "boots",
        "🧥 Плащ": "cloak",
        "🎒 Снаряжение": "backpack"
    },
    "💍 Аксессуары": {
        "💎 Серьги": "earrings",
        "📿 Ожерелье": "necklace",
        "💍 Кольца": "rings",
        "🧷 Пояс": "belt"
    },
    "🔮 Сферы": {
        "🟣 Разрушения": "destruction",
        "🟢 Защиты": "protection",
        "🟡 Мастерства": "mastery",
        "🔴 Жизни": "life",
        "🔵 Души": "soul"
    }
}

# Для аксессуаров вводим второй уровень — сначала выбирается тип аксессуара
# (Серьги / Кольца / Ожерелья / Пояс), затем — тематическая подгруппа внутри типа
ACCESSORY_SUBGROUPS = [
    "💎 Серьги",
    "💍 Кольца",
    "📿 Ожерелье",
    "🧷 Пояс",
]

# Тематические подгруппы, специфичные для каждого типа аксессуаров
ACCESSORY_TYPE_SUBGROUPS = {
    "💎 Серьги": [
        "СЛИЯНИЯ",
        "ЯРОСТЬ",
        "РАСПРАВА",
        "ГАРМОНИЯ",
        "ВОССТАНОВЛЕНИЕ",
        "ПОГЛОЩЕНИЕ",
        "УКЛОНЕНИЕ",
    ],
    "💍 Кольца": [
        "СЛИЯНИЯ",
        "АТАКА",
        "ЗАЩИТА",
        "ПАРАМЕТРЫ",
        "HP / MP",
        "ТЕЛЕПОРАЦИЯ",
        "ПЕРЕВОПЛОЩЕНИЯ",
    ],
    "📿 Ожерелье": [
        "СЛИЯНИЯ",
        "ЯРОСТЬ",
        "РАСПРАВА",
        "ГАРМОНИЯ",
        "ВОССТАНОВЛЕНИЕ",
        "ПОГЛОЩЕНИЕ",
        "УКЛОНЕНИЕ",
        "ПАРАМЕТРЫ",
        "HP / MP",
    ],
    "🧷 Пояс": [
        "СЛИЯНИЯ",
        "ЯРОСТЬ",
        "РАСПРАВА",
        "ГАРМОНИЯ",
        "ВОССТАНОВЛЕНИЕ",
        "ПОГЛОЩЕНИЕ",
        "УКЛОНЕНИЕ",
        "ПАРАМЕТРЫ",
        "HP / MP",
    ],
}

# Структура аксессуаров: для каждого типа указываем тематические подгруппы
# и точный список предметов, которые в них показываются.
ACCESSORY_STRUCTURE = {
    "💎 Серьги": {
        "СЛИЯНИЯ": [
            "Серьги Мушкетера",
            "Серьги Потрошителя",
            "Серьги Шпиона",
            "Серьги Витязя",
            "Серьги Варвара",
            "Серьги Атланта",
            "Серьги Вождя",
            "Серьги Колосса",
            "Серьги Авантюриста",
        ],
        "ЯРОСТЬ": [
            "Серьги Ярости",
            "Серьги Священной Ярости",
            "Серьги Праведной Ярости",
        ],
        "РАСПРАВА": [
            "Серьги Расправы",
            "Серьги Жестокой Расправы",
            "Серьги Беспощадной Расправы",
        ],
        "ГАРМОНИЯ": [
            "Серьги Гармонии",
            "Серьги Святой Гармонии",
            "Серьги Божественной Гармонии",
        ],
        "ВОССТАНОВЛЕНИЕ": [
            "Серьги Восстановления",
            "Серьги Улучшенного Восстановления",
            "Серьги Усиленного Восстановления",
        ],
        "ПОГЛОЩЕНИЕ": [
            "Серьги Поглощения",
            "Серьги Улучшенного Поглощения",
            "Серьги Усиленного Поглощения",
        ],
        "УКЛОНЕНИЕ": [
            "Серьги Уклонения",
            "Серьги Улучшенного Уклонения",
            "Серьги Усиленного Уклонения",
        ],
    },
    "💍 Кольца": {
        "СЛИЯНИЯ": [
            "Кольцо Берсерка",
            "Кольцо Головореза",
            "Кольцо Чернокнижника",
            "Кольцо Карателя",
            "Кольцо Охотника",
            "Кольцо Чародея",
            "Кольцо Пророка",
            "Кольцо Гладиатора",
            "Кольцо Фанатика",
            "Кольцо Ратника",
        ],
        "АТАКА": [
            "Кольцо Гнева",
            "Кольцо Атаки",
            "Кольцо Разрушения",
            "Кольцо Смертельной Атаки",
            "Кольцо Смелости",
            "Кольцо Преграды",
        ],
        "ЗАЩИТА": [
            "Кольцо Святого Поглощения",
            "Кольцо Божественного Поглощения",
            "Кольцо Холода",
            "Стеклянное Кольцо",
        ],
        "ПАРАМЕТРЫ": [
            "Кольцо Высокой Силы",
            "Кольцо Высокой Ловкости",
            "Кольцо Высокого Интеллекта",
            "Блестящее Кольцо Силы",
            "Блестящее Кольцо Ловкости",
            "Блестящее Кольцо Интеллекта",
            "Светящееся Кольцо Силы",
            "Светящееся Кольцо Ловкости",
            "Светящееся Кольцо Интеллекта",
        ],
        "HP / MP": [
            "Усиленное Кольцо Выживания",
            "Усиленное Кольцо Восстановления",
            "Улучшенное Кольцо Выживания",
            "Улучшенное Кольцо Восстановления",
        ],
        "ТЕЛЕПОРАЦИЯ": [
            "Кольцо Телепортации",
            "Редкое Кольцо Телепортации",
            "Эпическое Кольцо Телепортации",
            "Легендарное Кольцо Телепортации",
        ],
        "ПЕРЕВОПЛОЩЕНИЯ": [
            "Кольцо Перевоплощения",
            "Редкое Кольцо Перевоплощения",
            "Эпическое Кольцо Перевоплощения",
            "Легендарное Кольцо Перевоплощения",
        ],
    },
    "📿 Ожерелье": {
        "СЛИЯНИЯ": [
            "Ожерелье Берсерка",
            "Ожерелье Головореза",
            "Ожерелье Чернокнижника",
            "Ожерелье Карателя",
            "Ожерелье Охотника",
            "Ожерелье Чародея",
            "Ожерелье Пророка",
            "Ожерелье Гладиатора",
            "Ожерелье Фанатика",
            "Ожерелье Ратника",
        ],
        "ЯРОСТЬ": [
            "Ожерелье Ярости",
            "Ожерелье Священной Ярости",
            "Ожерелье Праведной Ярости",
        ],
        "РАСПРАВА": [
            "Ожерелье Расправы",
            "Ожерелье Жестокой Расправы",
            "Ожерелье Беспощадной Расправы",
        ],
        "ГАРМОНИЯ": [
            "Ожерелье Гармонии",
            "Ожерелье Святой Гармонии",
            "Ожерелье Божественной Гармонии",
        ],
        "ВОССТАНОВЛЕНИЕ": [
            "Ожерелье Восстановления",
            "Ожерелье Улучшенного Восстановления",
            "Ожерелье Усиленного Восстановления",
        ],
        "ПОГЛОЩЕНИЕ": [
            "Ожерелье Поглощения",
            "Ожерелье Улучшенного Поглощения",
            "Ожерелье Усиленного Поглощения",
        ],
        "УКЛОНЕНИЕ": [
            "Ожерелье Уклонения",
            "Ледяное Ожерелье",
            "Стеклянное Ожерелье",
        ],
        "ПАРАМЕТРЫ": [
            "Ожерелье Высокой Силы",
            "Ожерелье Высокой Ловкости",
            "Ожерелье Высокого Интеллекта",
            "Блестящее Ожерелье Силы",
            "Блестящее Ожерелье Ловкости",
            "Блестящее Ожерелье Интеллекта",
            "Светящееся Ожерелье Силы",
            "Светящееся Ожерелье Ловкости",
            "Светящееся Ожерелье Интеллекта",
        ],
        "HP / MP": [
            "Усиленное Ожерелье Выживания",
            "Усиленное Ожерелье Восстановления",
            "Улучшенное Ожерелье Выживания",
            "Улучшенное Ожерелье Восстановления",
        ],
    },
    "🧷 Пояс": {
        "СЛИЯНИЯ": [
            "Пояс Берсерка",
            "Пояс Головореза",
            "Пояс Чернокнижника",
            "Пояс Карателя",
            "Пояс Охотника",
            "Пояс Чародея",
            "Пояс Пророка",
            "Пояс Гладиатора",
            "Пояс Фанатика",
            "Пояс Ратника",
        ],
        "ЯРОСТЬ": [
            "Пояс Ярости",
            "Пояс Священной Ярости",
            "Пояс Праведной Ярости",
        ],
        "РАСПРАВА": [
            "Пояс Расправы",
            "Пояс Жестокой Расправы",
            "Пояс Беспощадной Расправы",
        ],
        "ГАРМОНИЯ": [
            "Пояс Гармонии",
            "Пояс Святой Гармонии",
            "Пояс Божественной Гармонии",
        ],
        "ВОССТАНОВЛЕНИЕ": [
            "Пояс Восстановления",
            "Пояс Улучшенного Восстановления",
            "Пояс Усиленного Восстановления",
        ],
        "ПОГЛОЩЕНИЕ": [
            "Пояс Поглощения",
            "Пояс Улучшенного Поглощения",
            "Пояс Усиленного Поглощения",
        ],
        "УКЛОНЕНИЕ": [
            "Пояс Уклонения",
            "Ледяной Пояс",
            "Стеклянный Пояс",
        ],
        "ПАРАМЕТРЫ": [
            "Пояс Высокой Силы",
            "Пояс Высокой Ловкости",
            "Пояс Высокого Интеллекта",
            "Блестящий Пояс Силы",
            "Блестящий Пояс Ловкости",
            "Блестящий Пояс Интеллекта",
            "Светящийся Пояс Силы",
            "Светящийся Пояс Ловкости",
            "Светящийся Пояс Интеллекта",
        ],
        "HP / MP": [
            "Усиленный Пояс Выживания",
            "Усиленный Пояс Восстановления",
            "Улучшенный Пояс Выживания",
            "Улучшенный Пояс Восстановления",
        ],
    },
}

# Precomputed category/subcategory helpers
# `CATEGORY_NAMES` is used for reply keyboards; `SUBCAT_MAP` maps subcategory text
# to (category_index, subcategory_index, category_text) for quick lookup.
CATEGORY_NAMES = list(MARKET_CATEGORIES.keys())

SUBCAT_MAP = {}
for _ci, _cat in enumerate(CATEGORY_NAMES):
    _subcats = list(MARKET_CATEGORIES[_cat].keys())
    for _si, _sub in enumerate(_subcats):
        SUBCAT_MAP[_sub] = (_ci, _si, _cat)


# ================== WEAPON DATA ==================

MELEE_WEAPONS = {
    1: ["Боевой Топор", "Хитиновая Сабля", "Кровавые Джамадхары", "Кровавый Клинок"],
    2: ["Морглай", "Копьё Гвардейца", "Англахель", "Клинок Отражения", "Аронди"],
    3: ["Двуручный Меч", "Железная Алебарда", "Эльфийский Меч", "Адские Катары", "Адский Клинок", "Меч Лунного Света"],
    4: ["Меч Правосудия", "Крис", "Меч Точности Рарки"],
    5: ["Дамасская Алебарда", "Слэшер", "Меч Жреца", "Джамадхары Убийцы", "Блестящий Меч Солнца"],
    6: ["Стальная Алебарда Метеоса", "Пылающий Двуручный Меч Метеоса", "Огненный Клеймор Метеоса", "Огненные Катары Метеоса", "Раскалённый Ятаган Метеоса", "Пламенная Рапира Метеоса"]
}

RANGED_WEAPONS = {
    1: ["Длинный Лук Ворона", "Охотничий Лук", "Скипетр Мудрости", "Орб Души Гайи"],
    2: ["Лук Гнома", "Бронебойное Ружьё", "Посох Литейн", "Орб Призывателя"],
    3: ["Эльфийский Лук", "Громовое Ружьё", "Посох Аллатариэль", "Орб Зефироса"],
    4: ["Кремниевое Ружьё", "Посох Югинеса", "Орб Юпитера"],
    5: ["Композитный Лук", "Карабин Гномов", "Скипетр Жреца", "Орб Воды"],
    6: ["Огненный Лук Метеоса", "Вулканический Мушкет Метеоса", "Священный Скипетр Метеоса", "Магмовый Орб Метеоса"]
}

# ================== EQUIPMENT DATA ==================

HELMETS = {
    1: ["Стальной Шлем", "Маска Тьмы"],
    2: ["Мифриловый Шлем", "Маска Велкена"],
    3: ["Магический Мифриловый Шлем", "Магическая Маска Велкена"],
    4: ["Шлем Ифрита", "Маска Энергии Ифрита", "Шлем Бафомета", "Маска Ярости Бафомета"]
}

ARMOR = {
    1: ["Железный Пластинчатый Доспех", "Кольчужный Доспех", "Доспех Тьмы"],
    2: ["Тяжелый Мифриловый Доспех", "Легкий Мифриловый Доспех", "Доспех Велкена"],
    3: ["Тяжелый Магический Мифриловый Доспех", "Легкий Магический Мифриловый Доспех", "Магический Доспех Велкена"],
    4: ["Тяжелый Доспех Ифрита", "Легкий Доспех Ифрита", "Доспех Энергии Ифрита", "Тяжелый Доспех Бафомета", "Легкий Доспех Бафомета", "Доспех Ярости Бафомета"]
}

GLOVES = {
    1: ["Стальные Перчатки", "Перчатки Тьмы"],
    2: ["Мифриловые Перчатки", "Перчатки Велкена"],
    3: ["Магические Мифриловые Перчатки", "Магические Перчатки Велкена"],
    4: ["Перчатки Ифрита", "Перчатки Энергии Ифрита", "Перчатки Бафомета", "Перчатки Ярости Бафомета"]
}

BOOTS = {
    1: ["Стальные Сапоги", "Сапоги Тьмы"],
    2: ["Мифриловые Сапоги", "Сапоги Велкена"],
    3: ["Магические Мифриловые Сапоги", "Магические Сапоги Велкена"],
    4: ["Сапоги Ифрита", "Сапоги Энергии Ифрита", "Сапоги Бафомета", "Сапоги Ярости Бафомета"]
}

CLOAKS = {
    1: ["Обычный Плащ"],
    2: ["Мифриловый Плащ"],
    3: ["Магический Мифриловый Плащ"],
    4: ["Плащ Ифрита", "Плащ Бафомета"]
}

BACKPACKS = {
    1: [
        "Средний Щит",
        "Колчан Стальных Стрел",
        "Стальной Камень Души",
        "Браслет Убийцы",
        "Браслет Хранителя",
    ],
    2: [
        "Большой Щит",
        "Колчан Мифриловых Стрел",
        "Мифриловый Камень Души",
        "Мифриловый Браслет Убийцы",
        "Мифриловый Браслет Хранителя",
    ],
    3: [
        "Щит Стража",
        "Костяной Щит",
        "Колчан Магических Стрел",
        "Магический Камень Души",
        "Магический Браслет Убийцы",
        "Магический Браслет Хранителя",
    ],
    4: [
        "Щит Ифрита",
        "Щит Бафомета",
        "Колчан Стрел Ифрита",
        "Колчан Стрел Бафомета",
        "Камень Души Ифрита",
        "Камень Души Бафомета",
        "Браслет Ифрита",
        "Браслет Бафомета",
    ]
}

# ================== ACCESSORIES DATA ==================

EARRINGS = {
    1: [
        "Серьги Мушкетера",
        "Серьги Потрошителя",
        "Серьги Шпиона",
        "Серьги Витязя",
        "Серьги Варвара",
        "Серьги Атланта",
        "Серьги Вождя",
        "Серьги Колосса",
        "Серьги Авантюриста",
        "Серьги Ярости",
        "Серьги Священной Ярости",
        "Серьги Праведной Ярости",
        "Серьги Расправы",
        "Серьги Жестокой Расправы",
        "Серьги Беспощадной Расправы",
        "Серьги Гармонии",
        "Серьги Святой Гармонии",
        "Серьги Божественной Гармонии",
        "Серьги Восстановления",
        "Серьги Улучшенного Восстановления",
        "Серьги Усиленного Восстановления",
        "Серьги Поглощения",
        "Серьги Улучшенного Поглощения",
        "Серьги Усиленного Поглощения",
        "Серьги Уклонения",
        "Серьги Улучшенного Уклонения",
        "Серьги Усиленного Уклонения",
    ]
}

NECKLACE = {
    1: [
        "Ожерелье Берсерка",
        "Ожерелье Головореза",
        "Ожерелье Чернокнижника",
        "Ожерелье Карателя",
        "Ожерелье Охотника",
        "Ожерелье Чародея",
        "Ожерелье Пророка",
        "Ожерелье Гладиатора",
        "Ожерелье Фанатика",
        "Ожерелье Ратника",
        "Ожерелье Ярости",
        "Ожерелье Священной Ярости",
        "Ожерелье Праведной Ярости",
        "Ожерелье Расправы",
        "Ожерелье Жестокой Расправы",
        "Ожерелье Беспощадной Расправы",
        "Ожерелье Гармонии",
        "Ожерелье Святой Гармонии",
        "Ожерелье Божественной Гармонии",
        "Ожерелье Восстановления",
        "Ожерелье Улучшенного Восстановления",
        "Ожерелье Усиленного Восстановления",
        "Ожерелье Поглощения",
        "Ожерелье Улучшенного Поглощения",
        "Ожерелье Усиленного Поглощения",
        "Ожерелье Уклонения",
        "Ледяное Ожерелье",
        "Стеклянное Ожерелье",
        "Ожерелье Высокой Силы",
        "Ожерелье Высокой Ловкости",
        "Ожерелье Высокого Интеллекта",
        "Блестящее Ожерелье Силы",
        "Блестящее Ожерелье Ловкости",
        "Блестящее Ожерелье Интеллекта",
        "Светящееся Ожерелье Силы",
        "Светящееся Ожерелье Ловкости",
        "Светящееся Ожерелье Интеллекта",
        "Усиленное Ожерелье Выживания",
        "Усиленное Ожерелье Восстановления",
        "Улучшенное Ожерелье Выживания",
        "Улучшенное Ожерелье Восстановления",
    ]
}

RINGS = {
    1: [
        "Кольцо Берсерка",
        "Кольцо Головореза",
        "Кольцо Чернокнижника",
        "Кольцо Карателя",
        "Кольцо Охотника",
        "Кольцо Чародея",
        "Кольцо Пророка",
        "Кольцо Гладиатора",
        "Кольцо Фанатика",
        "Кольцо Ратника",
        "Кольцо Телепортации",
        "Редкое Кольцо Телепортации",
        "Эпическое Кольцо Телепортации",
        "Легендарное Кольцо Телепортации",
        "Кольцо Перевоплощения",
        "Редкое Кольцо Перевоплощения",
        "Эпическое Кольцо Перевоплощения",
        "Легендарное Кольцо Перевоплощения",
        "Кольцо Гнева",
        "Кольцо Атаки",
        "Кольцо Разрушения",
        "Кольцо Смертельной Атаки",
        "Кольцо Смелости",
        "Кольцо Преграды",
        "Кольцо Святого Поглощения",
        "Кольцо Божественного Поглощения",
        "Кольцо Холода",
        "Стеклянное Кольцо",
        "Кольцо Высокой Силы",
        "Кольцо Высокой Ловкости",
        "Кольцо Высокого Интеллекта",
        "Блестящее Кольцо Силы",
        "Блестящее Кольцо Ловкости",
        "Блестящее Кольцо Интеллекта",
        "Светящееся Кольцо Силы",
        "Светящееся Кольцо Ловкости",
        "Светящееся Кольцо Интеллекта",
        "Усиленное Кольцо Выживания",
        "Усиленное Кольцо Восстановления",
        "Улучшенное Кольцо Выживания",
        "Улучшенное Кольцо Восстановления",
    ]
}

BELTS = {
    1: [
        "Пояс Берсерка",
        "Пояс Головореза",
        "Пояс Чернокнижника",
        "Пояс Карателя",
        "Пояс Охотника",
        "Пояс Чародея",
        "Пояс Пророка",
        "Пояс Гладиатора",
        "Пояс Фанатика",
        "Пояс Ратника",
        "Пояс Ярости",
        "Пояс Священной Ярости",
        "Пояс Праведной Ярости",
        "Пояс Расправы",
        "Пояс Жестокой Расправы",
        "Пояс Беспощадной Расправы",
        "Пояс Гармонии",
        "Пояс Святой Гармонии",
        "Пояс Божественной Гармонии",
        "Пояс Восстановления",
        "Пояс Улучшенного Восстановления",
        "Пояс Усиленного Восстановления",
        "Пояс Поглощения",
        "Пояс Улучшенного Поглощения",
        "Пояс Усиленного Поглощения",
        "Пояс Уклонения",
        "Ледяной Пояс",
        "Стеклянный Пояс",
        "Пояс Высокой Силы",
        "Пояс Высокой Ловкости",
        "Пояс Высокого Интеллекта",
        "Блестящий Пояс Силы",
        "Блестящий Пояс Ловкости",
        "Блестящий Пояс Интеллекта",
        "Светящийся Пояс Силы",
        "Светящийся Пояс Ловкости",
        "Светящийся Пояс Интеллекта",
        "Усиленный Пояс Выживания",
        "Усиленный Пояс Восстановления",
        "Улучшенный Пояс Выживания",
        "Улучшенный Пояс Восстановления",
    ]
}

# ================== SPHERES DATA ==================
# Новая система: Рары (1-4) и Уровни (1-5)
# Рары: 1=⚪ Обычная, 2=🔵 Редкая, 3=🟢 Эпическая, 4=🟣 Легендарная

SPHERE_RARITY_MAP = {
    1: "⚪ Обычная",
    2: "🔵 Редкая",
    3: "🟢 Эпическая",
    4: "🟣 Легендарная"
}

DESTRUCTION_SPHERES = {
    1: {
        1: ["Осколок Разрушения"],
        2: ["Фрагмент Разрушения"],
        3: ["Глаз Разрушения"],
        4: ["Ядро Разрушения"],
        5: ["Сущность Разрушения"],
    },
    2: {
        1: ["Осколок Разрушения"],
        2: ["Фрагмент Разрушения"],
        3: ["Глаз Разрушения"],
        4: ["Ядро Разрушения"],
        5: ["Сущность Разрушения"],
    },
    3: {
        1: ["Осколок Разрушения"],
        2: ["Фрагмент Разрушения"],
        3: ["Глаз Разрушения"],
        4: ["Ядро Разрушения"],
        5: ["Сущность Разрушения"],
    },
    4: {
        1: ["Осколок Разрушения"],
        2: ["Фрагмент Разрушения"],
        3: ["Глаз Разрушения"],
        4: ["Ядро Разрушения"],
        5: ["Абсолютное Разрушение"],
    }
}

PROTECTION_SPHERES = {
    1: {
        1: ["Осколок Защиты"],
        2: ["Фрагмент Защиты"],
        3: ["Щит Защиты"],
        4: ["Крепость Защиты"],
        5: ["Сущность Защиты"],
    },
    2: {
        1: ["Осколок Защиты"],
        2: ["Фрагмент Защиты"],
        3: ["Щит Защиты"],
        4: ["Крепость Защиты"],
        5: ["Сущность Защиты"],
    },
    3: {
        1: ["Осколок Защиты"],
        2: ["Фрагмент Защиты"],
        3: ["Щит Защиты"],
        4: ["Крепость Защиты"],
        5: ["Сущность Защиты"],
    },
    4: {
        1: ["Осколок Защиты"],
        2: ["Фрагмент Защиты"],
        3: ["Щит Защиты"],
        4: ["Крепость Защиты"],
        5: ["Абсолютная Защита"],
    }
}

MASTERY_SPHERES = {
    1: {
        1: ["Осколок Мастерства"],
        2: ["Фрагмент Мастерства"],
        3: ["Источник Мастерства"],
        4: ["Вершина Мастерства"],
        5: ["Сущность Мастерства"],
    },
    2: {
        1: ["Осколок Мастерства"],
        2: ["Фрагмент Мастерства"],
        3: ["Источник Мастерства"],
        4: ["Вершина Мастерства"],
        5: ["Сущность Мастерства"],
    },
    3: {
        1: ["Осколок Мастерства"],
        2: ["Фрагмент Мастерства"],
        3: ["Источник Мастерства"],
        4: ["Вершина Мастерства"],
        5: ["Сущность Мастерства"],
    },
    4: {
        1: ["Осколок Мастерства"],
        2: ["Фрагмент Мастерства"],
        3: ["Источник Мастерства"],
        4: ["Вершина Мастерства"],
        5: ["Абсолютное Мастерство"],
    }
}

LIFE_SPHERES = {
    1: {
        1: ["Осколок Жизни"],
        2: ["Фрагмент Жизни"],
        3: ["Источник Жизни"],
        4: ["Сердце Жизни"],
        5: ["Сущность Жизни"],
    },
    2: {
        1: ["Осколок Жизни"],
        2: ["Фрагмент Жизни"],
        3: ["Источник Жизни"],
        4: ["Сердце Жизни"],
        5: ["Сущность Жизни"],
    },
    3: {
        1: ["Осколок Жизни"],
        2: ["Фрагмент Жизни"],
        3: ["Источник Жизни"],
        4: ["Сердце Жизни"],
        5: ["Сущность Жизни"],
    },
    4: {
        1: ["Осколок Жизни"],
        2: ["Фрагмент Жизни"],
        3: ["Источник Жизни"],
        4: ["Сердце Жизни"],
        5: ["Абсолютная Жизнь"],
    }
}

SOUL_SPHERES = {
    1: {
        1: ["Осколок Души"],
        2: ["Фрагмент Души"],
        3: ["Отражение Души"],
        4: ["Глубина Души"],
        5: ["Сущность Души"],
    },
    2: {
        1: ["Осколок Души"],
        2: ["Фрагмент Души"],
        3: ["Отражение Души"],
        4: ["Глубина Души"],
        5: ["Сущность Души"],
    },
    3: {
        1: ["Осколок Души"],
        2: ["Фрагмент Души"],
        3: ["Отражение Души"],
        4: ["Глубина Души"],
        5: ["Сущность Души"],
    },
    4: {
        1: ["Осколок Души"],
        2: ["Фрагмент Души"],
        3: ["Отражение Души"],
        4: ["Глубина Души"],
        5: ["Абсолютная Душа"],
    }
}

ITEMS_DATABASE = {
    "🗡️ Ближнее": MELEE_WEAPONS,
    "🏹 Дальнее": RANGED_WEAPONS,
    "🪖 Шлем": HELMETS,
    "🦺 Доспех": ARMOR,
    "🧤 Перчатки": GLOVES,
    "👢 Сапоги": BOOTS,
    "🧥 Плащ": CLOAKS,
    "🎒 Снаряжение": BACKPACKS,
    "💎 Серьги": EARRINGS,
    "📿 Ожерелье": NECKLACE,
    "💍 Кольца": RINGS,
    "🧷 Пояс": BELTS,
    "� Разрушения": DESTRUCTION_SPHERES,
    "💚 Защиты": PROTECTION_SPHERES,
    "� Мастерства": MASTERY_SPHERES,
    "🔴 Жизни": LIFE_SPHERES,
    "🔵 Души": SOUL_SPHERES,
}


def max_rank_for_subcategory(subcategory):
    """Return maximum available rank for a given subcategory.
    Equipment subcategories are limited to rank 1..4; others support 1..6.
    """
    equipment_subcats = {
        "🪖 Шлем",
        "🦺 Доспех",
        "🧤 Перчатки",
        "👢 Сапоги",
        "🧥 Плащ",
        "🎒 Снаряжение",
    }
    # Spheres use rarities/levels rather than ranks; limit them to 1..4 here
    if subcategory in equipment_subcats or is_sphere(subcategory):
        return 4
    return 6

def is_sphere(subcategory):
    """Check if the given subcategory is a sphere type."""
    sphere_subcats = {
        "🟣 Разрушения",
        "🟢 Защиты",
        "🟡 Мастерства",
        "🔴 Жизни",
        "🔵 Души",
    }
    return subcategory in sphere_subcats

def get_sphere_db(subcategory):
    """Get the sphere database for a given subcategory."""
    sphere_map = {
        "🟣 Разрушения": DESTRUCTION_SPHERES,
        "🟢 Защиты": PROTECTION_SPHERES,
        "🟡 Мастерства": MASTERY_SPHERES,
        "🔴 Жизни": LIFE_SPHERES,
        "🔵 Души": SOUL_SPHERES,
    }
    return sphere_map.get(subcategory, {})


def get_accessory_items_by_keyword(keyword, accessory_type=None):
    """Возвращает плоский список названий предметов для заданной темы.
    Если передан `accessory_type` (один из ключей ACCESSORY_STRUCTURE),
    поиск берётся только в этой группе; иначе — агрегируется по всем типам.
    """
    key = keyword.strip()
    results = []

    if accessory_type and accessory_type in ACCESSORY_STRUCTURE:
        subgroup_map = ACCESSORY_STRUCTURE.get(accessory_type, {})
        items = subgroup_map.get(key, [])
        results.extend(items)
        return results

    # Если тип не указан — ищем во всех типах: собираем все совпадения по подгруппе
    for atype, subgroup_map in ACCESSORY_STRUCTURE.items():
        items = subgroup_map.get(key, [])
        if items:
            results.extend(items)

    # Fallback: если ничего не найдено в структуре — попытаемся найти по вхождению
    if not results:
        keyword_lower = key.lower()
        for db in (EARRINGS, NECKLACE, RINGS, BELTS):
            for rank_items in db.values():
                for itm in rank_items:
                    try:
                        if keyword_lower in itm.lower():
                            results.append(itm)
                    except Exception:
                        continue

    return results

@dp.message(F.text == "👀 Просмотреть товары")
async def market_view_msg(msg: Message):
    if await is_banned(msg.from_user.id):
        await msg.answer("⛔ <b>Доступ запрещён</b>\nВы временно заблокированы и не можете пользоваться рынком.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return
    await msg.answer(TEXT['market_view_category'], reply_markup=reply_kb(*CATEGORY_NAMES, "⬅ ГЛАВНОЕ МЕНЮ"))

@dp.message(MarketFSM.create_category, F.text.in_(CATEGORY_NAMES))
async def market_create_cat_msg(msg: Message, state: FSMContext):
    # Handler for category selection during creation flow
    cat = msg.text
    if cat not in CATEGORY_NAMES:
        return
    cat_idx = CATEGORY_NAMES.index(cat)
    await state.update_data(category=cat, cat_idx=cat_idx)
    # Если выбраны аксессуары — сначала показываем тематические подгруппы
    if cat == "💍 Аксессуары":
        await msg.answer(f"📂 {cat}\n\nВыберите тему аксессуаров:", reply_markup=reply_kb(*ACCESSORY_SUBGROUPS, "⬅ Назад"))
    else:
        subcats = list(MARKET_CATEGORIES[cat].keys())
        await msg.answer(f"📂 {cat}\n\nВыберите подкатегорию:", reply_markup=reply_kb(*subcats, "⬅ Назад"))
    await state.set_state(MarketFSM.create_subcategory)


@dp.message(MarketFSM.create_subcategory)
async def market_create_subcat_msg(msg: Message, state: FSMContext):
    """Message-based handler for subcategory selection during creation flow.
    This fixes the reply-keyboard path which previously stalled after selecting a subcategory.
    """
    text = msg.text
    if text == "⬅ Назад":
        # Return to category selection
        await msg.answer(TEXT['market_create_main'], reply_markup=reply_kb(*CATEGORY_NAMES, "⬅ Назад"))
        await state.set_state(MarketFSM.create_category)
        return

    data = await state.get_data()
    category = data.get('category')
    if not category:
        return await msg.answer("Неверная подкатегория.", reply_markup=reply_kb("⬅ Назад"))

    # Если пользователь выбрал тип аксессуара (Серьги/Кольца/Ожерелье/Пояс)
    if category == "💍 Аксессуары" and text in ACCESSORY_SUBGROUPS:
        accessory_type = text
        await state.update_data(subcategory=accessory_type, accessory_type=accessory_type)
        subgroups = ACCESSORY_TYPE_SUBGROUPS.get(accessory_type, [])
        if not subgroups:
            await msg.answer("В этой категории нет тем.", reply_markup=reply_kb("⬅ Назад", "⬅ ГЛАВНОЕ МЕНЮ"))
            return
        await msg.answer(
            f"📂 {accessory_type}\n\nВыберите тему аксессуаров:",
            reply_markup=reply_kb(*subgroups, "⬅ Назад")
        )
        await state.set_state(MarketFSM.create_subcategory)
        return

    # Если пользователь выбрал тему внутри ранее выбранного типа аксессуара
    data_local = await state.get_data()
    accessory_type = data_local.get('accessory_type')
    if category == "💍 Аксессуары" and accessory_type and text in ACCESSORY_TYPE_SUBGROUPS.get(accessory_type, []):
        theme = text
        await state.update_data(subcategory=theme)
        items = get_accessory_items_by_keyword(theme, accessory_type)
        if not items:
            await msg.answer("В этой теме нет предметов.", reply_markup=reply_kb("⬅ Назад", "⬅ ГЛАВНОЕ МЕНЮ"))
            return
        # Показываем предметы через reply кнопки
        buttons = items + ["⬅ Отмена"]
        await msg.answer(
            f"{accessory_type} — <b>{theme}</b>\n\nВыберите предмет:",
            reply_markup=reply_kb(*buttons)
        )
        await state.set_state(MarketFSM.create_weapon_selection)
        return

    subcategory = text
    await state.update_data(subcategory=subcategory)

    subcat_value = MARKET_CATEGORIES[category].get(subcategory)

    # Weapon path -> show rank selection (reply buttons)
    if subcat_value in ("melee", "ranged"):
        weapon_type = subcat_value
        await state.update_data(weapon_type=weapon_type)
        buttons = [f"Ранг {i}" for i in range(1, 7)] + ["⬅ Отмена"]
        weapon_category = "Ближнее" if weapon_type == "melee" else "Дальнее"
        await msg.answer(
            f"⚔️ <b>Оружие: {weapon_category}</b>\n\nРанг I - VI\n\nВыберите ранг оружия:",
            reply_markup=reply_kb(*buttons)
        )
        await state.set_state(MarketFSM.create_weapon_rank)
        return

    # Sphere path -> choose RARITY (reply buttons)
    if is_sphere(subcategory):
        buttons = [SPHERE_RARITY_MAP[i] for i in range(1, 5)] + ["⬅ Отмена"]
        await msg.answer(
            f"🔮 <b>{subcategory}</b>\n\nВыберите редкость (Редкость I - IV):",
            reply_markup=reply_kb(*buttons)
        )
        await state.set_state(MarketFSM.create_weapon_rank)
        return

    # Non-weapon, non-sphere path -> accessories: skip rank selection and show items directly
    if category == "💍 Аксессуары":
        items_db = ITEMS_DATABASE.get(subcategory, {})
        items = items_db.get(1, [])
        if not items:
            await msg.answer("В этой подкатегории нет предметов.", reply_markup=reply_kb("⬅ Назад", "⬅ ГЛАВНОЕ МЕНЮ"))
            return
        buttons = items + ["⬅ Отмена"]
        await msg.answer(
            f"💍 <b>{subcategory}</b>\n\nВыберите предмет:",
            reply_markup=reply_kb(*buttons)
        )
        await state.set_state(MarketFSM.create_weapon_selection)
        return

    # Non-accessories: choose rank for the subcategory
    max_rank = max_rank_for_subcategory(subcategory)
    buttons = [f"Ранг {i}" for i in range(1, max_rank + 1)] + ["⬅ Отмена"]
    rank_range_label = "I - IV" if max_rank == 4 else "I - VI"
    await msg.answer(
        f"🎁 <b>Выберите ранг</b>\n\nРанг {rank_range_label}\n\nВыберите ранг предмета:",
        reply_markup=reply_kb(*buttons)
    )
    await state.set_state(MarketFSM.create_weapon_rank)

@dp.message(MarketFSM.create_weapon_rank, F.text.startswith("Ранг"))
async def market_weapon_rank_msg(msg: Message, state: FSMContext):
    """Выбор ранга оружия или экипировки"""
    try:
        rank = int(msg.text.split()[-1])
    except:
        await msg.answer("⚠️ Пожалуйста, выберите ранг из предложенных.")
        return
    
    data = await state.get_data()
    weapon_type = data.get('weapon_type')
    category = data.get('category')
    subcategory = data.get('subcategory')
    
    if weapon_type:
        # Это выбор ранга оружия
        await state.update_data(weapon_rank=rank)
        if weapon_type == "melee":
            weapons = MELEE_WEAPONS.get(rank, [])
        else:
            weapons = RANGED_WEAPONS.get(rank, [])
        
        if not weapons:
            await msg.answer("В этом ранге нет оружия.", reply_markup=reply_kb("⬅ Отмена"))
            return
        
        buttons = list(weapons) + ["⬅ Отмена"]
        weapon_category = "Ближнее" if weapon_type == "melee" else "Дальнее"
        rank_label = "METEOS" if rank == 6 else str(rank)
        
        await msg.answer(
            f"⚔️ <b>Оружие: {weapon_category}</b>\n\nРанг {rank_label}\n\nВыберите оружие:",
            reply_markup=reply_kb(*buttons)
        )
        await state.set_state(MarketFSM.create_weapon_selection)
    else:
        # Это выбор ранга экипировки/аксессуаров
        await state.update_data(item_rank=rank)
        items_db = ITEMS_DATABASE.get(subcategory, {})
        items = items_db.get(rank, [])
        
        if not items:
            await msg.answer("В этом ранге нет предметов.", reply_markup=reply_kb("⬅ Отмена"))
            return
        
        buttons = list(items) + ["⬅ Отмена"]
        rank_label = "METEOS" if rank == 6 else str(rank)
        
        await msg.answer(
            f"🎁 <b>{subcategory}</b>\n\nРанг {rank_label}\n\nВыберите предмет:",
            reply_markup=reply_kb(*buttons)
        )
        await state.set_state(MarketFSM.create_weapon_selection)

@dp.message(MarketFSM.create_weapon_rank, F.text.in_([SPHERE_RARITY_MAP[i] for i in range(1,5)]))
async def market_sphere_rarity_msg(msg: Message, state: FSMContext):
    """Выбор редкости сферы"""
    data = await state.get_data()
    subcategory = data.get('subcategory')
    
    # Проверяем это ли выбор редкости сферы
    if not is_sphere(subcategory):
        return
    
    rarity = None
    for i in range(1, 5):
        if SPHERE_RARITY_MAP[i] in msg.text:
            rarity = i
            break
    
    if rarity is None:
        await msg.answer("⚠️ Пожалуйста, выберите редкость из предложенных.")
        return
    
    await state.update_data(sphere_rarity=rarity)
    
    # Показываем выбор уровня (1-5)
    buttons = [f"Уровень {i}" for i in range(1, 6)] + ["⬅ Отмена"]
    
    await msg.answer(
        f"🔮 <b>{subcategory}</b>\n\n"
        f"Редкость: {SPHERE_RARITY_MAP[rarity]}\n\n"
        "Выберите уровень сферы:",
        reply_markup=reply_kb(*buttons)
    )

@dp.message(MarketFSM.create_weapon_rank, F.text.startswith("Уровень"))
async def market_sphere_level_msg(msg: Message, state: FSMContext):
    """Выбор уровня сферы"""
    try:
        level = int(msg.text.split()[-1])
    except:
        await msg.answer("⚠️ Пожалуйста, выберите уровень из предложенных.")
        return
    
    data = await state.get_data()
    subcategory = data.get('subcategory')
    rarity = data.get('sphere_rarity')
    
    if not rarity:
        await msg.answer("Ошибка: редкость не выбрана.", reply_markup=reply_kb("⬅ Отмена"))
        return
    
    # Сохраняем уровень и формируем generick-имя элемента без показа конкретных названий
    await state.update_data(sphere_level=level, item_name=f"Уровень {level}")

    # Для сфер сразу показываем выбор заточки (без шага выбора конкретного названия)
    max_enchant = 5
    buttons = [f"+{i}" for i in range(0, max_enchant + 1)] + ["⬅ Отмена"]

    await msg.answer(
        f"🔧 <b>Выбор заточки</b>\n\n"
        f"{SPHERE_RARITY_MAP[rarity]} | Уровень {level}\n\n"
        f"Выберите заточку предмета (от +0 до +{max_enchant}):",
        reply_markup=reply_kb(*buttons)
    )
    await state.set_state(MarketFSM.create_enchant)

@dp.message(MarketFSM.create_weapon_selection, F.text != "⬅ Отмена")
async def market_item_selected_msg(msg: Message, state: FSMContext):
    """Выбор предмета/оружия/сферы"""
    item_name = msg.text
    await state.update_data(item_name=item_name)
    
    data = await state.get_data()
    weapon_type = data.get('weapon_type')
    category = data.get('category')
    is_sphere_item = data.get('sphere_rarity') is not None
    accessory_type = data.get('accessory_type')
    theme = data.get('subcategory')
    
    # Determine enchant behaviour:
    # - Spheres: +0..+5
    # - Weapons: +0..+14
    # - Accessories: all types with theme `СЛИЯНИЯ` get +0..+5; other themes skip enchant
    if is_sphere_item:
        max_enchant = 5
    elif weapon_type or 'Оружие' in (category or ''):
        max_enchant = 14
    elif category == "💍 Аксессуары":
        # For all accessory types, if theme is "СЛИЯНИЯ", show enchant selection
        if theme == "СЛИЯНИЯ":
            max_enchant = 5
        else:
            # Other themes: skip enchant selection
            await msg.answer(TEXT['market_enter_price'], reply_markup=reply_kb("⬅ Отмена"))
            await state.set_state(MarketFSM.create_price)
            return
    else:
        max_enchant = 14

    # Show enchant selection
    buttons = [f"+{i}" for i in range(0, max_enchant + 1)] + ["⬅ Отмена"]

    await msg.answer(
        f"🔧 <b>Выбор заточки</b>\n\n"
        f"Выберите заточку предмета (от +0 до +{max_enchant}):",
        reply_markup=reply_kb(*buttons)
    )
    await state.set_state(MarketFSM.create_enchant)

@dp.message(MarketFSM.create_weapon_selection, F.text == "⬅ Отмена")
async def market_cancel_selection(msg: Message, state: FSMContext):
    """Отмена выбора предмета"""
    await state.clear()
    await msg.answer("❌ <b>Создание объявления отменено</b>", reply_markup=reply_kb("🛒 РЫНОК", "⬅ ГЛАВНОЕ МЕНЮ"))

@dp.message(F.text.in_(list(SUBCAT_MAP.keys())))
async def market_listings_msg(msg: Message, state: FSMContext):
    # Show listings for chosen subcategory (from keyboard)
    current_state = await state.get_state()
    if current_state and current_state.startswith("MarketFSM:"):
        # Skip this handler if in any market FSM state
        return
    if msg.text not in SUBCAT_MAP:
        return
    ci, si, category = SUBCAT_MAP[msg.text]
    subcats = list(MARKET_CATEGORIES[category].keys())
    subcategory = subcats[si]

    listings = await get_listings_by_category(category, subcategory)
    if not listings:
        await msg.answer(TEXT['market_no_listings'], reply_markup=reply_kb("⬅ Назад", "⬅ ГЛАВНОЕ МЕНЮ"))
        return

    try:
        await msg.delete()
    except:
        pass

    for item_id, item_name, price, seller_username, user_id, runes, enchant, expires_at, listing_type in listings:
        text = await create_listing_text(
            item_id,
            item_name,
            price,
            seller_username,
            user_id,
            runes=runes,
            enchant=enchant,
            is_admin=(msg.from_user.id == ADMIN_ID),
            category=category,
            subcategory=subcategory,
            status="⏳ Активное",
            expires_at=expires_at,
            listing_type=listing_type
        )
        # Use inline buttons on listings (not reply keyboard)
        buttons = [
            ("👤 Мой профиль", f"seller_profile:{user_id}")
        ]
        if msg.from_user.id == ADMIN_ID:
            buttons.extend([
                ("🗑️ Удалить", f"admin_del_listing:{item_id}"),
                ("🚫 Забанить", f"admin_ban_seller:{user_id}")
            ])
        buttons.append(("⬅ Назад", "market_view"))
        await msg.answer(text, reply_markup=inline_kb(buttons))


async def get_active_listings_count(user_id):
    """Получить количество активных объявлений пользователя"""
    result = await db_exec(
        "SELECT COUNT(*) FROM market_listings WHERE user_id=? AND status='active'",
        (user_id,), True, True
    )
    return result[0] if result else 0

async def get_listings_by_category(category, subcategory):
    """Получить объявления по категории и подкатегории"""
    rows = await db_exec(
        "SELECT id, item_name, price, seller_username, user_id, runes, enchant, expires_at, listing_type FROM market_listings "
        "WHERE category=? AND subcategory=? AND status='active' ORDER BY created_at DESC",
        (category, subcategory), True
    )
    return rows or []

async def search_listings_by_name(search_query):
    """Получить объявления по названию товара"""
    search_pattern = f"%{search_query}%"
    rows = await db_exec(
        "SELECT id, item_name, price, seller_username, user_id, runes, enchant, category, subcategory, expires_at, listing_type FROM market_listings "
        "WHERE item_name LIKE ? AND status='active' ORDER BY created_at DESC",
        (search_pattern,), True
    )
    return rows or []

async def add_slot_penalty(user_id, slot_number, reason):
    """Добавить штраф на один конкретный слот (3 часа)"""
    penalty_until = int(time.time()) + 3 * 60 * 60
    await db_exec(
        "INSERT OR REPLACE INTO listing_slot_penalty (user_id, slot_number, penalty_until, reason) VALUES (?,?,?,?)",
        (user_id, slot_number, penalty_until, reason)
    )

async def get_slot_penalties(user_id):
    """Получить все штрафы на слоты пользователя"""
    result = await db_exec(
        "SELECT slot_number, penalty_until FROM listing_slot_penalty WHERE user_id=?",
        (user_id,), True
    )
    return result or []

async def remove_expired_slot_penalties(user_id):
    """Удалить истекшие штрафы на слоты"""
    current_time = int(time.time())
    await db_exec(
        "DELETE FROM listing_slot_penalty WHERE user_id=? AND penalty_until < ?",
        (user_id, current_time)
    )

async def is_slot_penalized(user_id, slot_number):
    """Проверить, закрыт ли конкретный слот штрафом"""
    result = await db_exec(
        "SELECT penalty_until FROM listing_slot_penalty WHERE user_id=? AND slot_number=?",
        (user_id, slot_number), True, True
    )
    if not result:
        return False
    return result[0] > int(time.time())

async def add_listing_penalty(user_id, reason):
    """Добавить штраф на создание объявлений (3 часа)"""
    penalty_until = int(time.time()) + 3 * 60 * 60
    await db_exec(
        "INSERT OR REPLACE INTO listing_creation_penalty (user_id, penalty_until, reason) VALUES (?,?,?)",
        (user_id, penalty_until, reason)
    )

async def has_listing_penalty(user_id):
    """Проверить есть ли штраф на создание объявлений"""
    result = await db_exec(
        "SELECT penalty_until FROM listing_creation_penalty WHERE user_id=?",
        (user_id,), True, True
    )
    if not result:
        return False
    return result[0] > int(time.time())

async def remove_expired_listings():
    """Удалить истекшие объявления (автоудаление через 24 часа)"""
    current_time = int(time.time())
    # Удаляем объявления, у которых истёк таймер (expires_at < текущее время)
    await db_exec(
        "DELETE FROM market_listings WHERE expires_at IS NOT NULL AND expires_at < ?",
        (current_time,)
    )

async def format_time_remaining(expires_at):
    """Форматировать оставшееся время до истечения объявления"""
    if expires_at is None:
        return None
    remaining = expires_at - int(time.time())
    if remaining <= 0:
        return "истекло"
    hours = remaining // 3600
    minutes = (remaining % 3600) // 60
    if hours > 0:
        return f"{hours}ч {minutes}мин"
    else:
        return f"{minutes}мин"

async def create_listing_text(item_id, item_name, price, seller_username, user_id, runes=None, enchant=None, is_admin=False, category=None, subcategory=None, status=None, sphere_rarity=None, sphere_level=None, expires_at=None, listing_type=None):
    """Создать текст объявления в нужном порядке и формате:
    1) Линия квадратиков сверху (зелёные для ПРОДАМ, красные для КУПЛЮ)
    2) Тип объявления (ПРОДАМ или КУПЛЮ)
    3) Название (жирным) + заточка справа золотом
    4) Руны
    5) Цена (толстым, с красным маркером)
    6) Категория / Подкатегория
    7) Статус
    8) Линия квадратиков снизу
    """
    # Определить тип объявления и цвет квадратиков
    if listing_type == "BUY":
        listing_type_text = "❌ КУПЛЮ"
        squares = "🟥" * 12
    else:
        listing_type_text = "✅ ПРОДАМ"
        squares = "🟩" * 12
    
    # Начало текста с верхней линией квадратиков
    text = f"{squares}\n"
    
    # Тип объявления
    if listing_type:
        text += f"<b>{listing_type_text}</b>\n"
    
    # Enchant (заточка) — справа от названия золотом (🟡 золотой цвет)
    # Enchant (заточка) — показываем маркерами/иконками вместо простого числа
    # Для аксессуаров с подгруппой "СЛИЯНИЯ" показываем заточку, для остальных не показываем
    if category == "💍 Аксессуары" and subcategory != "СЛИЯНИЯ":
        enchant_str = ""
    else:
        enchant_str = enchant_marker(enchant)
    
    # Для сфер форматируем название красиво: редкость + уровень
    if is_sphere(subcategory) and sphere_rarity is not None:
        rarity_name = SPHERE_RARITY_MAP[sphere_rarity]
        display_name = f"{rarity_name} {item_name}"
    else:
        display_name = item_name
    
    text += f"📦 <b>{display_name}</b>{enchant_str}\n"

    # Runes (if available)
    if runes:
        text += f"🔮 <b>Руны:</b> {format_runes(runes)}\n"
    # Seller
    text += f"👤 <b>Продавец:</b> {seller_username}\n"

    # Category / Subcategory
    if category and subcategory:
        text += f"📂 <b>{category} / {subcategory}</b>\n"
    elif category:
        text += f"📂 <b>{category}</b>\n"

    # Status (последним)
    if status:
        text += f"📌 <b>Статус:</b> {status}\n"

    # Timer (таймер истечения объявления)
    if expires_at is not None:
        time_remaining = await format_time_remaining(expires_at)
        if time_remaining:
            text += f"⏱️ <b>Истекает через:</b> {time_remaining}\n"

    # Admin info last
    if is_admin:
        text += f"🆔 <b>UID:</b> {user_id}\n"

    # Price (moved to the bottom by request)
    if price is not None:
        text += f"💰 <b>Цена:</b> {price_marker(price)}\n"
    
    # Нижняя линия квадратиков
    text += f"{squares}"

    return text


@dp.message(F.text.startswith("🛒 РЫНОК"))
async def market_main(msg: Message):
    """Главное меню Рынка"""
    if await is_banned(msg.from_user.id):
        await msg.answer("⛔ Вы заблокированы и не можете пользоваться рынком.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return
    
    await msg.answer(
        TEXT['market_main'],
        reply_markup=reply_kb("👀 Просмотреть товары", "📝 Подать Объявление", "🔍 Поиск по названию", "📦 Мои объявления", "⬅ ГЛАВНОЕ МЕНЮ")
    )

@dp.message(MarketFSM.create_listing_type, F.text.in_(["✅ ПРОДАМ", "❌ КУПЛЮ"]))
async def market_select_listing_type(msg: Message, state: FSMContext):
    """Выбор типа объявления (ПРОДАМ или КУПЛЮ)"""
    listing_type = "SELL" if msg.text == "✅ ПРОДАМ" else "BUY"
    await state.update_data(listing_type=listing_type)
    await msg.answer(TEXT['market_create_main'], reply_markup=reply_kb(*CATEGORY_NAMES, "⬅ Отмена"))
    await state.set_state(MarketFSM.create_category)

@dp.message(F.text == "👀 Просмотреть товары")
async def market_view(msg: Message):
    """Просмотр товаров - выбор категории"""
    await msg.answer(
        TEXT['market_view_category'],
        reply_markup=reply_kb(*CATEGORY_NAMES, "⬅ ГЛАВНОЕ МЕНЮ")
    )

@dp.message(F.text.in_(CATEGORY_NAMES), ~F.state(MarketFSM.create_category))
async def market_subcategory(msg: Message, state: FSMContext):
    # Browsing categories -> show subcategories (NOT in creation mode)
    current_state = await state.get_state()
    if current_state and current_state.startswith("MarketFSM:"):
        # Skip this handler if in any market FSM state
        return
    cat = msg.text
    if cat not in MARKET_CATEGORIES:
        return
    subcats = list(MARKET_CATEGORIES[cat].keys())
    await msg.answer(f"{cat}\n\nВыберите подкатегорию:", reply_markup=reply_kb(*subcats, "⬅ Назад", "⬅ ГЛАВНОЕ МЕНЮ"))



@dp.message(F.text == "📝 Подать Объявление")
async def market_create_msg(msg: Message, state: FSMContext):
    if await is_banned(msg.from_user.id):
        await msg.answer("⛔ <b>Доступ запрещён</b>\nВы временно заблокированы и не можете создавать объявления.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return

    # Очистить истекшие штрафы на слоты перед проверкой
    await remove_expired_slot_penalties(msg.from_user.id)
    
    active_count = await get_active_listings_count(msg.from_user.id)
    
    # Проверить, доступны ли свободные слоты (не под штрафом)
    penalties = await get_slot_penalties(msg.from_user.id)
    penalized_slots = set(slot for slot, _ in penalties)
    
    # Найти первый свободный слот
    available_slot = None
    for slot in range(1, 6):  # Слоты 1..5
        if slot not in penalized_slots and slot > active_count:
            available_slot = slot
            break
    
    if available_slot is None and active_count >= 5:
        await msg.answer(TEXT['market_listing_limit'], reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return
    
    if available_slot is None:
        # Все слоты закрыты штрафами
        penalty_details = []
        for slot, penalty_until in penalties:
            remaining = penalty_until - int(time.time())
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            penalty_details.append(f"Слот {slot}: {hours}ч {minutes}мин")
        
        await msg.answer(
            f"⏱️ <b>Все доступные слоты закрыты штрафами</b>\n\n" +
            "\n".join(penalty_details),
            reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
        )
        return

    await state.clear()
    await state.update_data(user_id=msg.from_user.id)
    await msg.answer(
        "📝 <b>Подать Объявление</b>\n\n"
        "Выберите тип объявления:",
        reply_markup=reply_kb("✅ ПРОДАМ", "❌ КУПЛЮ", "⬅ Отмена")
    )
    await state.set_state(MarketFSM.create_listing_type)


@dp.callback_query(F.data == "market_preview_confirm")
async def market_confirm_create_cb(cb: CallbackQuery, state: FSMContext):
    """Создание объявления через inline кнопку"""
    await cb.answer()
    data = await state.get_data()
    seller_username = f"@{cb.from_user.username}" if cb.from_user.username else f"id:{cb.from_user.id}"
    runes = data.get('runes')
    runes_str = ','.join(runes) if runes else None
    enchant_val = data.get('enchant')
    listing_type = data.get('listing_type', 'SELL')
    expires_at = int(time.time()) + 24 * 60 * 60  # 24 часа
    await db_exec(
        "INSERT INTO market_listings (user_id, category, subcategory, item_name, price, runes, enchant, status, created_at, seller_username, expires_at, listing_type) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            cb.from_user.id,
            data['category'],
            data['subcategory'],
            data['item_name'],
            data['price'],
            runes_str,
            enchant_val,
            'active',
            int(time.time()),
            seller_username,
            expires_at,
            listing_type
        )
    )
    await cb.message.edit_text("✅ <b>Объявление успешно опубликовано</b>\nСпасибо — оно появилось в каталоге.", reply_markup=inline_kb([("⬅ ГЛАВНОЕ МЕНЮ", "back_to_menu")]))
    await state.clear()


@dp.callback_query(F.data == "market_preview_cancel")
async def market_cancel_create_cb(cb: CallbackQuery, state: FSMContext):
    """Отмена создания объявления через inline кнопку"""
    await cb.answer()
    await cb.message.edit_text("❌ <b>Размещение отменено</b>\nЕсли нужно — начните заново.", reply_markup=inline_kb([("⬅ ГЛАВНОЕ МЕНЮ", "back_to_menu")]))
    await state.clear()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_cb(cb: CallbackQuery, state: FSMContext):
    """Возврат в главное меню из сообщений маркетплейса"""
    await cb.answer()
    await state.clear()
    
    buttons = [
        "🛒 РЫНОК (💜BETA💜)",
        "💱 ПРОВЕРИТЬ КУРС",
        "📂 МОИ АКТИВНЫЕ СДЕЛКИ",
        "📜 ИСТОРИЯ",
    ]
    if cb.from_user.id == ADMIN_ID:
        buttons = ["🛠 АДМИН ПАНЕЛЬ"] + [b for b in buttons if b not in ("💱 ПРОВЕРИТЬ КУРС", "📂 МОИ АКТИВНЫЕ СДЕЛКИ")]
    else:
        buttons = ["💴 ПРОДАТЬ СЕРЕБРО В ГРН", "💵 ПРОДАТЬ СЕРЕБРО В USDT"] + buttons + ["ℹ️ Инфо и Правила"]
    if cb.from_user.id == ADMIN_ID:
        buttons.insert(4, "🧹 ОЧИСТИТЬ АКТИВНЫЕ ЗАКАЗЫ")
    
    await cb.message.delete()
    await cb.message.answer(
        TEXT['menu_title'],
        reply_markup=reply_kb(*buttons)
    )


@dp.callback_query(F.data == "market_preview_edit")
async def market_edit_listing_cb(cb: CallbackQuery, state: FSMContext):
    """Редактирование цены через inline кнопку"""
    await cb.answer()
    await cb.message.edit_text("💰 <b>Введите новую цену (в кк):</b>", reply_markup=inline_kb([("⬅ Назад", "market_preview_back")]))
    await state.set_state(MarketFSM.edit_price)

@dp.message(MarketFSM.edit_price)
async def market_edit_price(msg: Message, state: FSMContext):
    """Обновление цены и возврат к предпросмотру"""
    try:
        price = int(msg.text)
    except:
        return await msg.answer(TEXT['enter_number_error'])
    
    data = await state.get_data()
    await state.update_data(price=price)
    
    item_name = data.get('item_name')
    category = data.get('category')
    subcategory = data.get('subcategory')
    seller_username = f"@{msg.from_user.username}" if msg.from_user.username else f"id:{msg.from_user.id}"
    runes = data.get('runes')
    enchant = data.get('enchant')
    listing_type = data.get('listing_type', 'SELL')

    preview_body = await create_listing_text(
        None,
        item_name,
        price,
        seller_username,
        msg.from_user.id,
        runes=runes,
        enchant=enchant,
        category=category,
        subcategory=subcategory,
        status="Предпросмотр",
        listing_type=listing_type
    )

    text = f"👁️ <b>Предпросмотр объявления</b>\n\n{preview_body}\nПроверьте данные и подтвердите создание объявления."

    buttons = [
        ("✅ СОЗДАТЬ", "market_preview_confirm"),
        ("🔄 ИЗМЕНИТЬ", "market_preview_edit"),
        ("❌ ОТМЕНИТЬ", "market_preview_cancel")
    ]

    await msg.answer(text, reply_markup=inline_kb(buttons))
    await state.set_state(MarketFSM.create_preview)

@dp.callback_query(F.data == "market_preview_back")
async def market_preview_back(cb: CallbackQuery, state: FSMContext):
    """Возврат к предпросмотру из редактирования"""
    await cb.answer()
    data = await state.get_data()
    
    item_name = data.get('item_name')
    category = data.get('category')
    subcategory = data.get('subcategory')
    price = data.get('price')
    seller_username = f"@{cb.from_user.username}" if cb.from_user.username else f"id:{cb.from_user.id}"
    runes = data.get('runes')
    enchant = data.get('enchant')
    sphere_rarity = data.get('sphere_rarity')
    listing_type = data.get('listing_type', 'SELL')

    preview_body = await create_listing_text(
        None,
        item_name,
        price,
        seller_username,
        cb.from_user.id,
        runes=runes,
        enchant=enchant,
        category=category,
        subcategory=subcategory,
        status="Предпросмотр",
        sphere_rarity=sphere_rarity,
        listing_type=listing_type
    )

    text = f"👁️ <b>Предпросмотр объявления</b>\n\n{preview_body}\nПроверьте данные и подтвердите создание объявления."

    buttons = [
        ("✅ СОЗДАТЬ", "market_preview_confirm"),
        ("🔄 ИЗМЕНИТЬ", "market_preview_edit"),
        ("❌ ОТМЕНИТЬ", "market_preview_cancel")
    ]

    await cb.message.edit_text(text, reply_markup=inline_kb(buttons))
    await state.set_state(MarketFSM.create_preview)


@dp.message(F.text == "📦 Мои объявления")
async def market_my_msg(msg: Message):
    active_count = await get_active_listings_count(msg.from_user.id)
    limit_text = f"{active_count}/5"
    
    text = f"{TEXT['market_my_listings']}\n\n📊 <b>Лимит объявлений:</b> {limit_text}"
    
    await msg.answer(
        text,
        reply_markup=reply_kb("⏳ Активные", "⚠️ Мои штрафы", "⬅ Назад")
    )

@dp.message(F.text == "🔍 Поиск по названию")
async def market_search_msg(msg: Message, state: FSMContext):
    """Начало поиска по названию"""
    if await is_banned(msg.from_user.id):
        await msg.answer("⛔ <b>Доступ запрещён</b>\nВы временно заблокированы и не можете пользоваться рынком.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return
    await msg.answer(TEXT['market_search_prompt'], reply_markup=reply_kb("⬅ Отмена"))
    await state.set_state(MarketFSM.search_query)

@dp.message(MarketFSM.search_query, F.text != "⬅ Отмена")
async def market_search_results(msg: Message, state: FSMContext):
    """Поиск товаров по названию"""
    search_text = msg.text.strip()
    
    if not search_text:
        await msg.answer("⚠️ Пожалуйста, введите название товара или ключевое слово.")
        return
    
    # Поиск в базе данных
    listings = await search_listings_by_name(search_text)
    
    if not listings:
        await msg.answer(TEXT['market_search_no_results'], reply_markup=reply_kb("👀 Просмотреть товары", "🔍 Поиск по названию", "⬅ ГЛАВНОЕ МЕНЮ"))
        await state.clear()
        return
    
    # Показываем результаты поиска
    result_text = f"🔍 <b>Результаты поиска: \"{search_text}\"</b>\n\nНайдено {len(listings)} объявлений:\n\n"
    
    buttons = []
    for idx, listing in enumerate(listings[:10]):  # Показываем максимум 10 результатов
        item_id, item_name, price, seller_username, user_id, runes, enchant, category, subcategory, expires_at, listing_type = listing
        result_text += await create_listing_text(item_id, item_name, price, seller_username, user_id, runes, enchant, category=category, subcategory=subcategory, expires_at=expires_at, listing_type=listing_type)
        result_text += "\n" + "─" * 30 + "\n"
        buttons.append((f"📤 {item_name[:25]}", f"market_item:{item_id}"))
    
    if len(listings) > 10:
        result_text += f"\n...и ещё {len(listings) - 10} объявлений"
    
    buttons.append(("🔍 Новый поиск", "market_search"))
    buttons.append(("⬅ ГЛАВНОЕ МЕНЮ", "back_to_menu"))
    
    await msg.answer(result_text, reply_markup=inline_kb(buttons))
    await state.clear()

@dp.message(MarketFSM.search_query, F.text == "⬅ Отмена")
async def market_search_cancel(msg: Message, state: FSMContext):
    """Отмена поиска"""
    await state.clear()
    await msg.answer(TEXT['market_main'], reply_markup=reply_kb("👀 Просмотреть товары", "📝 Подать Объявление", "🔍 Поиск по названию", "📦 Мои объявления", "⬅ ГЛАВНОЕ МЕНЮ"))


# Обработчик для кнопки "⬅ Назад" из меню "Мои объявления"
@dp.message(F.text == "⬅ Назад")
async def my_listings_back(msg: Message):
    """Возврат из меню объявлений в главное меню"""
    await msg.answer(
        TEXT['menu_title'],
        reply_markup=reply_kb(
            "🛒 РЫНОК (💜BETA💜)",
            "💱 ПРОВЕРИТЬ КУРС",
            "📂 МОИ АКТИВНЫЕ СДЕЛКИ",
            "📜 ИСТОРИЯ",
            "ℹ️ Инфо и Правила"
        )
    )

@dp.message(F.text == "⏳ Активные")
async def my_active_listings(msg: Message):
    """Активные объявления пользователя"""
    listings = await db_exec(
        "SELECT id, item_name, price, category, subcategory, runes, enchant, expires_at, listing_type FROM market_listings "
        "WHERE user_id=? AND status='active' ORDER BY created_at DESC",
        (msg.from_user.id,), True
    )
    
    if not listings:
        await msg.answer(
            "⏳ <b>Активные объявления</b>\n\n"
            "У вас нет активных объявлений.",
            reply_markup=reply_kb("⬅ Назад")
        )
        return
    
    # Показываем объявления
    seller_username = f"@{msg.from_user.username}" if msg.from_user.username else f"id:{msg.from_user.id}"
    for item_id, item_name, price, category, subcategory, runes, enchant, expires_at, listing_type in listings:
        text = await create_listing_text(
            item_id,
            item_name,
            price,
            seller_username,
            msg.from_user.id,
            runes=runes,
            enchant=enchant,
            category=category,
            subcategory=subcategory,
            status="⏳ Активное",
            expires_at=expires_at,
            listing_type=listing_type
        )

        await msg.answer(
            text,
            reply_markup=inline_kb([
                ("🗑️ Удалить", f"delete_listing:{item_id}"),
                ("⬅ Назад", "my_listings_menu")
            ])
        )

@dp.message(F.text == "⚠️ Мои штрафы")
async def my_penalties_msg(msg: Message):
    """Показать штрафы пользователя на слоты"""
    # Очистить истекшие штрафы перед отображением
    await remove_expired_slot_penalties(msg.from_user.id)
    
    penalties = await get_slot_penalties(msg.from_user.id)
    
    if not penalties:
        await msg.answer(
            "✅ <b>Мои штрафы</b>\n\n"
            "У вас нет активных штрафов. Все слоты доступны!",
            reply_markup=reply_kb("⬅ Назад")
        )
        return
    
    text = "⚠️ <b>Мои штрафы</b>\n\n"
    current_time = int(time.time())
    
    for slot_number, penalty_until in penalties:
        remaining = penalty_until - current_time
        if remaining > 0:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            text += f"🔒 <b>Слот {slot_number}:</b> {hours}ч {minutes}мин {seconds}сек\n"
    
    text += "\n📌 <i>Штрафованные слоты закрыты на 3 часа после удаления объявления</i>"
    
    await msg.answer(
        text,
        reply_markup=reply_kb("⬅ Назад")
    )

@dp.callback_query(F.data == "my_listings_menu")
async def my_listings_menu_cb(cb: CallbackQuery):
    """Возврат в меню объявлений"""
    await cb.answer()
    active_count = await get_active_listings_count(cb.from_user.id)
    limit_text = f"{active_count}/5"
    
    text = f"{TEXT['market_my_listings']}\n\n📊 <b>Лимит объявлений:</b> {limit_text}"
    
    await cb.message.edit_text(
        text,
        reply_markup=inline_kb([
            ("⏳ Активные", "market_active_listings"),
            ("⚠️ Мои штрафы", "market_my_penalties"),
            ("⬅ Назад", "back_to_menu")
        ])
    )

@dp.callback_query(F.data == "market_active_listings")
async def market_active_listings_cb(cb: CallbackQuery):
    """Показать активные объявления через callback"""
    await cb.answer()
    listings = await db_exec(
        "SELECT id, item_name, price, category, subcategory, runes, enchant, expires_at, listing_type FROM market_listings "
        "WHERE user_id=? AND status='active' ORDER BY created_at DESC",
        (cb.from_user.id,), True
    )
    
    if not listings:
        await cb.message.edit_text(
            "⏳ <b>Активные объявления</b>\n\n"
            "У вас нет активных объявлений.",
            reply_markup=inline_kb([("⬅ Назад", "my_listings_menu")])
        )
        return
    
    # Показываем объявления
    seller_username = f"@{cb.from_user.username}" if cb.from_user.username else f"id:{cb.from_user.id}"
    for item_id, item_name, price, category, subcategory, runes, enchant, expires_at, listing_type in listings:
        text = await create_listing_text(
            item_id,
            item_name,
            price,
            seller_username,
            cb.from_user.id,
            runes=runes,
            enchant=enchant,
            category=category,
            subcategory=subcategory,
            status="⏳ Активное",
            expires_at=expires_at,
            listing_type=listing_type
        )

        await cb.message.answer(
            text,
            reply_markup=inline_kb([
                ("🗑️ Удалить", f"delete_listing:{item_id}"),
                ("⬅ Назад", "my_listings_menu")
            ])
        )

@dp.callback_query(F.data == "market_my_penalties")
async def market_my_penalties_cb(cb: CallbackQuery):
    """Показать штрафы пользователя на слоты через callback"""
    await cb.answer()
    penalties = await get_slot_penalties(cb.from_user.id)
    
    if not penalties:
        await cb.message.edit_text(
            "⚠️ <b>Мои штрафы</b>\n\n"
            "У вас нет активных штрафов на слоты.",
            reply_markup=inline_kb([("⬅ Назад", "my_listings_menu")])
        )
        return
    
    penalty_text = "⚠️ <b>Мои штрафы на слоты</b>\n\n"
    for slot, penalty_until in penalties:
        remaining = penalty_until - int(time.time())
        if remaining > 0:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            penalty_text += f"Слот {slot}: {hours}ч {minutes}мин\n"
    
    await cb.message.edit_text(
        penalty_text,
        reply_markup=inline_kb([("⬅ Назад", "my_listings_menu")])
    )


































@dp.message(F.text == "⬅ Отмена", MarketFSM.create_price)
async def market_cancel_price(msg: Message, state: FSMContext):
    """Отмена ввода цены"""
    await state.clear()
    await msg.answer(
        "❌ <b>Создание объявления отменено</b>",
        reply_markup=reply_kb("🛒 РЫНОК", "⬅ ГЛАВНОЕ МЕНЮ")
    )

@dp.message(F.text == "⬅ Отмена", MarketFSM.create_enchant)
async def market_cancel_enchant(msg: Message, state: FSMContext):
    """Отмена выбора заточки"""
    await state.clear()
    await msg.answer("❌ <b>Создание объявления отменено</b>", reply_markup=reply_kb("🛒 РЫНОК", "⬅ ГЛАВНОЕ МЕНЮ"))

@dp.message(MarketFSM.create_enchant)
async def market_enchant_msg(msg: Message, state: FSMContext):
    """Выбор заточки через reply кнопки"""
    try:
        lvl = int(msg.text.replace("+", ""))
    except:
        await msg.answer("⚠️ Пожалуйста, выберите заточку из предложенных вариантов.")
        return

    await state.update_data(enchant=lvl)
    data = await state.get_data()

    # If this is a weapon (weapon_type set) or category contains 'Оружие', go to runes
    if data.get('weapon_type') or 'Оружие' in (data.get('category') or ''):
        await state.update_data(runes=[])
        text = (
            "🔮 <b>Выбор рун</b>\n\n"
            "Выберите руны, которые есть в вашем предмете.\n\n"
            "Выбрано: 0/5"
        )
        buttons = ["Ⅰ ⚪", "Ⅱ 🟡", "Ⅲ 🟢", "Ⅳ 🔵", "Ⅴ 🟣", "➡️ Следующий шаг", "⬅ Отмена"]
        await msg.answer(text, reply_markup=reply_kb(*buttons))
        await state.set_state(MarketFSM.create_runes)
    else:
        # Non-weapon: proceed to price input
        await msg.answer(TEXT['market_enter_price'], reply_markup=reply_kb("⬅ Отмена"))
        await state.set_state(MarketFSM.create_price)

@dp.message(MarketFSM.create_runes, F.text.in_(["Ⅰ ⚪", "Ⅱ 🟡", "Ⅲ 🟢", "Ⅳ 🔵", "Ⅴ 🟣", "➡️ Следующий шаг", "⬅ Отмена"]))
async def rune_select_msg(msg: Message, state: FSMContext):
    """Handle rune button presses through reply keyboard"""
    data = await state.get_data()
    runes = data.get('runes', []) or []
    
    if msg.text == "Ⅰ ⚪" and len(runes) < 5:
        runes.append("1")
        await state.update_data(runes=runes)
    elif msg.text == "Ⅱ 🟡" and len(runes) < 5:
        runes.append("2")
        await state.update_data(runes=runes)
    elif msg.text == "Ⅲ 🟢" and len(runes) < 5:
        runes.append("3")
        await state.update_data(runes=runes)
    elif msg.text == "Ⅳ 🔵" and len(runes) < 5:
        runes.append("4")
        await state.update_data(runes=runes)
    elif msg.text == "Ⅴ 🟣" and len(runes) < 5:
        runes.append("5")
        await state.update_data(runes=runes)
    elif msg.text == "➡️ Следующий шаг":
        await msg.answer(TEXT['market_enter_price'], reply_markup=reply_kb("⬅ Отмена"))
        await state.set_state(MarketFSM.create_price)
        return
    elif msg.text == "⬅ Отмена":
        await state.clear()
        await msg.answer("❌ <b>Создание объявления отменено</b>", reply_markup=reply_kb("🛒 РЫНОК", "⬅ ГЛАВНОЕ МЕНЮ"))
        return

    disp = format_runes(runes)
    text = (
        "🔮 <b>Выбор рун</b>\n\n"
        "Выберите руны, которые есть в вашем предмете.\n\n"
        f"Выбрано: {len(runes)}/5\n"
    )
    if disp:
        text += f"\nВыбранные руны: {disp}"

    buttons = ["Ⅰ ⚪", "Ⅱ 🟡", "Ⅲ 🟢", "Ⅳ 🔵", "Ⅴ 🟣", "➡️ Следующий шаг", "⬅ Отмена"]
    await msg.answer(text, reply_markup=reply_kb(*buttons))

@dp.message(MarketFSM.create_price)
async def market_preview(msg: Message, state: FSMContext):
    """Предпросмотр объявления"""
    try:
        price = int(msg.text)
    except:
        return await msg.answer(TEXT['enter_number_error'])
    
    data = await state.get_data()
    await state.update_data(price=price)
    
    item_name = data.get('item_name')
    category = data.get('category')
    subcategory = data.get('subcategory')
    seller_username = f"@{msg.from_user.username}" if msg.from_user.username else f"id:{msg.from_user.id}"
    runes = data.get('runes')
    enchant = data.get('enchant')
    sphere_rarity = data.get('sphere_rarity')
    listing_type = data.get('listing_type', 'SELL')

    preview_body = await create_listing_text(
        None,
        item_name,
        price,
        seller_username,
        msg.from_user.id,
        runes=runes,
        enchant=enchant,
        category=category,
        subcategory=subcategory,
        status="Предпросмотр",
        sphere_rarity=sphere_rarity,
        listing_type=listing_type
    )

    text = f"👁️ <b>Предпросмотр объявления</b>\n\n{preview_body}\nПроверьте данные и подтвердите создание объявления."
    
    buttons = [
        ("✅ СОЗДАТЬ", "market_preview_confirm"),
        ("🔄 ИЗМЕНИТЬ", "market_preview_edit"),
        ("❌ ОТМЕНИТЬ", "market_preview_cancel")
    ]
    
    await msg.answer(
        text,
        reply_markup=inline_kb(buttons)
    )
    await state.set_state(MarketFSM.create_preview)



# Completed/rejected listings handlers removed — only 'active' remains

@dp.callback_query(F.data.startswith("delete_listing:"))
async def delete_listing(cb: CallbackQuery):
    """Удаление объявления"""
    await cb.answer()
    item_id = int(cb.data.split(":")[1])
    
    # Проверка что это объявление пользователя
    listing = await db_exec(
        "SELECT user_id, item_name FROM market_listings WHERE id=?",
        (item_id,), True, True
    )
    
    if not listing or listing[0] != cb.from_user.id:
        await cb.answer("Ошибка: объявление не найдено или это не ваше объявление.", show_alert=True)
        return
    
    user_id = listing[0]
    item_name = listing[1]
    
    # Получить количество активных объявлений пользователя
    active_count = await get_active_listings_count(user_id)
    
    # Определяем номер слота для штрафа (считаем от активных объявлений)
    # Если у пользователя есть активные объявления, штраф ложится на один из них
    if active_count > 0:
        # Штраф ложится на один из слотов (1..5)
        slot_number = active_count  # Если 3 активных - штраф на слот 3
        await add_slot_penalty(user_id, slot_number, "user_deleted")
    
    # Удаляем объявление
    await db_exec("DELETE FROM market_listings WHERE id=?", (item_id,))
    
    if active_count > 0:
        await cb.message.edit_text(
            "🗑️ <b>Объявление удалено</b>\n\n"
            f"⏱️ <b>Штраф:</b> Слот {active_count} закрыт на 3 часа.",
            reply_markup=inline_kb([("⬅ Назад", "my_listings_menu")])
        )
    else:
        await cb.message.edit_text(
            "🗑️ <b>Объявление удалено</b>",
            reply_markup=inline_kb([("⬅ Назад", "my_listings_menu")])
        )

@dp.callback_query(F.data.startswith("seller_profile:"))
async def seller_profile(cb: CallbackQuery):
    """Профиль продавца - открыть в Telegram"""
    await cb.answer()
    seller_id = int(cb.data.split(":")[1])
    await cb.message.answer(
        "👤 Профиль продавца:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="🔗 ОТКРЫТЬ ПРОФИЛЬ",
                    url=f"tg://user?id={seller_id}"
                )
            ]]
        )
    )



@dp.callback_query(F.data.startswith("admin_del_listing:"))
async def admin_delete_listing(cb: CallbackQuery):
    """Админ удаляет объявление"""
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Нет доступа", show_alert=True)
        return
    
    item_id = int(cb.data.split(":")[1])
    await db_exec("DELETE FROM market_listings WHERE id=?", (item_id,))
    await cb.answer("🗑️ Объявление удалено", show_alert=True)

@dp.callback_query(F.data.startswith("admin_ban_seller:"))
async def admin_ban_seller(cb: CallbackQuery):
    """Админ банит продавца"""
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Нет доступа", show_alert=True)
        return
    
    user_id = int(cb.data.split(":")[1])
    until = int(time.time()) + 60 * 60
    
    await db_exec(
        "INSERT OR REPLACE INTO users (user_id, banned_until) VALUES (?,?)",
        (user_id, until)
    )
    
    await log_admin(cb.from_user.id, "ban_seller_market", str(user_id))
    await cb.answer(f"🚫 Пользователь {user_id} забанен на 60 минут", show_alert=True)






# ================== MENU ==================

@dp.message(F.text == "/start")
@dp.message(F.text == "⬅ ГЛАВНОЕ МЕНЮ")
async def menu(msg: Message):
    buttons = [
            "🛒 РЫНОК (💜BETA💜)",
            "💱 ПРОВЕРИТЬ КУРС",
            "📂 МОИ АКТИВНЫЕ СДЕЛКИ",
            "📜 ИСТОРИЯ",
    ]
    if msg.from_user.id == ADMIN_ID:
        # Для админа скрываем кнопки, относящиеся к пользовательской части
        buttons = ["🛠 АДМИН ПАНЕЛЬ"] + [b for b in buttons if b not in ("💱 ПРОВЕРИТЬ КУРС", "📂 МОИ АКТИВНЫЕ СДЕЛКИ")]
    else:
        # Для обычных пользователей: два отдельных раздела для подачи заявки
        buttons = ["💴 ПРОДАТЬ СЕРЕБРО В ГРН", "💵 ПРОДАТЬ СЕРЕБРО В USDT"] + buttons + ["ℹ️ Инфо и Правила"]
    if msg.from_user.id == ADMIN_ID:
        buttons.insert(4, "🧹 ОЧИСТИТЬ АКТИВНЫЕ ЗАКАЗЫ")
    await msg.answer(
        TEXT['menu_title'],
        reply_markup=reply_kb(*buttons)
    )

# ================== STATIC ==================

@dp.message(F.text == "💱 ПРОВЕРИТЬ КУРС")
async def rate(msg: Message):
    await msg.answer(
        TEXT['rate'].format(uah=RATE_UAH, usdt=RATE_USDT),
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )

@dp.message(F.text == "ℹ️ Инфо и Правила")
async def about(msg: Message):
    await msg.answer(
        "ℹ️ <b>ИНФОРМАЦИЯ И ПРАВИЛА</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>📌 ЧТО ЗДЕСЬ?</b>\n"
        "Этот бот — сервис для безопасного проведения сделок в R2 Online. "
        "На боте вы можете продавать серебро и пользоваться маркетплейсом для купли-продажи предметов.\n\n"
        "<b>💰 ОПЛАТЫ И СДЕЛКИ</b>\n"
        "⚠️ <b>ВСЕ оплаты и подтверждения проходят ТОЛЬКО В ИГРЕ</b>\n"
        "• Бот НЕ принимает реальные платежи\n"
        "• Бот НЕ хранит ценности\n"
        "• Администратор контролирует безопасность сделки\n\n"
        "<b>🛒 РЫНОК (МАРКЕТПЛЕЙС)</b>\n"
        "На маркетплейсе вы можете:\n"
        "• Выставлять до 5 активных объявлений\n"
        "• Продавать предметы из игры\n"
        "• Просматривать объявления других игроков\n"
        "• Общаться с покупателями\n\n"
        "<b>⚠️ ШТРАФЫ И САНКЦИИ</b>\n\n"
        "🚫 <b>Удаление собственного объявления</b>\n"
        "• Штраф: 3 часа на один из пяти слотов объявлений\n"
        "• Закрытый слот не может быть использован 3 часа\n"
        "• Остальные 4 слота остаются доступны\n\n"
        "⛔ <b>Ложные/Фиктивные сделки</b>\n"
        "• Попытка обмана администратора\n"
        "• Игра с отмены сделок без причины\n"
        "• Результат: <b>Временный или постоянный БАН</b> от 1 часа до вечного блока\n\n"
        "<b>📋 ОБЩИЕ ПРАВИЛА</b>\n"
        "✅ Будьте честны и вежливы\n"
        "✅ Выполняйте обещания\n"
        "✅ Используйте бот по назначению\n"
        "❌ Не создавайте фиктивные сделки\n"
        "❌ Не спамьте и не оскорбляйте\n"
        "❌ Не пытайтесь обойти систему\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📞 Вопросы? Обращайтесь к администратору",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )

# ================== ACTIVE DEALS ==================

@dp.message(F.text == "📂 МОИ АКТИВНЫЕ СДЕЛКИ")
async def my_active(msg: Message):
    rows = await db_exec(
        "SELECT id,status,amount_kk,currency FROM deals "
        "WHERE user_id=? AND status='in_work'",
        (msg.from_user.id,), True
    )
    if not rows:
        return await msg.answer("📂 У вас нет активных сделок.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    for did, st, kk, cur in rows:
        await msg.answer(
            f"📂 <b>Сделка #{did}</b>\n"
            f"📦 {kk_fmt(kk)}\n"
            f"📌 Статус: <i>{st}</i>",
            reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
        )

# ================== HISTORY ==================

@dp.message(F.text == "📜 ИСТОРИЯ")
async def history(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        rows = await db_exec(
            "SELECT id,user_id,amount_kk,currency FROM deals "
            "WHERE status='done' ORDER BY id DESC LIMIT 10",
            fetch=True
        )
        if not rows:
            return await msg.answer("📜 История пуста.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        text = "📜 <b>История заказов (ADMIN)</b>\n\n"
        for did, uid, kk, cur in rows:
            text += f"#{did} | UID {uid} | {kk_fmt(kk)} | {sum_fmt(cur,kk)}\n"
    else:
        rows = await db_exec(
            "SELECT id,amount_kk,currency FROM deals "
            "WHERE user_id=? AND status='done' ORDER BY id DESC LIMIT 10",
            (msg.from_user.id,), True
        )
        if not rows:
            return await msg.answer("📜 История пуста.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        text = "📜 <b>История сделок</b>\n\n"
        for did, kk, cur in rows:
            text += f"#{did} — {kk_fmt(kk)} — {sum_fmt(cur,kk)}\n"
    await msg.answer(text, reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))



# ================== DEAL CREATION ==================

@dp.message(F.text == "💴 ПРОДАТЬ СЕРЕБРО В ГРН")
async def create_uah(msg: Message, state: FSMContext):
    await state.clear()
    await state.update_data(server="R2 Rise", currency="UAH")
    await msg.answer(
        "Выберите банк:",
        reply_markup=reply_kb("Приват24", "Монобанк", "Другие", "⬅ ГЛАВНОЕ МЕНЮ")
    )
    await state.set_state(DealFSM.bank)


@dp.message(F.text == "💵 ПРОДАТЬ СЕРЕБРО В USDT")
async def create_usdt(msg: Message, state: FSMContext):
    await state.clear()
    await state.update_data(server="R2 Rise", currency="USDT")
    await msg.answer(
        "Выберите сеть:",
        reply_markup=reply_kb("Binance ID", "BEP20", "TRC20", "⬅ ГЛАВНОЕ МЕНЮ")
    )
    await state.set_state(DealFSM.usdt_net)

@dp.message(DealFSM.currency)
async def choose_currency(msg: Message, state: FSMContext):
    if msg.text == "💴 ГРН":
        await state.update_data(currency="UAH")
        await msg.answer("Выберите банк:", reply_markup=reply_kb("Приват24", "Монобанк", "Другие", "⬅ ГЛАВНОЕ МЕНЮ"))
        await state.set_state(DealFSM.bank)
    elif msg.text == "💵 USDT":
        await state.update_data(currency="USDT")
        await msg.answer("Выберите сеть:", reply_markup=reply_kb("Binance ID", "BEP20", "TRC20", "⬅ ГЛАВНОЕ МЕНЮ"))
        await state.set_state(DealFSM.usdt_net)

@dp.message(DealFSM.bank)
async def choose_bank(msg: Message, state: FSMContext):
    await state.update_data(bank=msg.text)
    await msg.answer("Введите инициалы:", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    await state.set_state(DealFSM.initials)

@dp.message(DealFSM.initials)
async def initials(msg: Message, state: FSMContext):
    await state.update_data(initials=msg.text)
    await msg.answer("Введите количество (кк):", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    await state.set_state(DealFSM.amount)

@dp.message(DealFSM.usdt_net)
async def choose_net(msg: Message, state: FSMContext):
    await state.update_data(usdt_net=msg.text)
    await msg.answer("Введите количество (кк):", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    await state.set_state(DealFSM.amount)


@dp.message(DealFSM.amount)
async def amount(msg: Message, state: FSMContext):
    try:
        k = int(msg.text)
    except:
        return await msg.answer(TEXT["enter_number_error"])
    data = await state.get_data()

    if data.get("currency") == "UAH" and k < SERVER_LIMITS['R2 Rise']['UAH_MIN']:
        return await msg.answer("Минимум 10кк.")
    if data.get("usdt_net") == "BEP20" and k < SERVER_LIMITS['R2 Rise']['USDT_BEP20_MIN']:
        return await msg.answer("Минимум 10кк.")
    if data.get("usdt_net") == "TRC20" and k < SERVER_LIMITS['R2 Rise']['USDT_TRC20_MIN']:
        return await msg.answer("Минимум 50кк.")

    await state.update_data(amount=k)

    preview_text = (
        "📝 <b>Предосмотр заявки</b>\n\n"
        f"💱 Валюта: <b>{data.get('currency')}</b>\n"
        f"🏦 Банк / сеть: <b>{data.get('bank') or data.get('usdt_net')}</b>\n"
        f"✍️ Инициалы: <b>{data.get('initials')}</b>\n"
        f"📦 Количество: <b>{kk_fmt(k)}</b>\n"
        f"💰 Сумма: <b>{sum_fmt(data.get('currency'), k)}</b>\n\n"
        "Проверьте данные заявки."
    )

    await msg.answer(
        preview_text,
        reply_markup=inline_kb([
            ("✅ ПОДТВЕРЖДАЮ", "deal_confirm"),
            ("🔄 ВЕРНУТЬСЯ В НАЧАЛО", "deal_restart")
        ])
    )
    await state.set_state(DealFSM.preview)


# ================== ADMIN / BUYER CHAIN ==================
# (same as production version, unchanged)

@dp.message(DealFSM.admin_time)
async def save_time(msg: Message, state: FSMContext):
    deal_id = (await state.get_data())["deal_id"]
    await db_exec("UPDATE deals SET deal_time=?, status=? WHERE id=?", (msg.text, "time_set", deal_id))
    uid = (await db_exec("SELECT user_id FROM deals WHERE id=?", (deal_id,), True, True))[0]
    await bot.send_message(
        uid,
        f"⏱ Время сделки: <b>{msg.text}</b>",
        reply_markup=inline_kb([
            ("✅ ПОДТВЕРДИТЬ", f"confirm:{deal_id}"),
            ("❌ ОТМЕНИТЬ", f"user_cancel:{deal_id}")
        ])
    )
    await state.clear()

@dp.message(DealFSM.admin_nick)
async def save_nick(msg: Message, state: FSMContext):
    deal_id = (await state.get_data())["deal_id"]
    await db_exec(
        "UPDATE deals SET nick=?, status=?, timer_until=? WHERE id=?",
        (msg.text, "nick_set", int(time.time()) + TIMER_SECONDS, deal_id)
    )
    uid = (await db_exec("SELECT user_id FROM deals WHERE id=?", (deal_id,), True, True))[0]
    await bot.send_message(
        uid,
        f"👤 Ник для сделки: <b>{msg.text}</b>\nСоздайте сделку в игре.",
        reply_markup=inline_kb([("🟢 СДЕЛКУ СОЗДАЛ", f"created:{deal_id}")])
    )
    await state.clear()

@dp.message(F.text == "🧹 ОЧИСТИТЬ АКТИВНЫЕ ЗАКАЗЫ")
async def admin_clear_active(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    rows = await db_exec(
        "SELECT DISTINCT user_id FROM deals "
        "WHERE status='in_work'",
        fetch=True
    )

    if not rows:
        return await msg.answer(
            "🧹 Активных сделок нет.",
            reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
        )

    count = 0
    for (uid,) in rows:
        await db_exec(
            "UPDATE deals SET status='cancelled' "
            "WHERE user_id=? AND status='in_work'",
            (uid,)
        )
        await db_exec(
            "INSERT OR IGNORE INTO users (user_id,banned_until) VALUES (?,0)",
            (uid,)
        )
        count += 1

    await msg.answer(
        f"🧹 <b>Очистка завершена</b>\n"
        f"Пользователей очищено: <b>{count}</b>",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )



# ================== CANCEL DEAL ==================


@dp.callback_query(F.data.startswith("accept:"))
async def admin_accept(cb: CallbackQuery):
    deal_id = int(cb.data.split(":")[1])
    await cb.answer()
    await db_exec("UPDATE deals SET status='in_work' WHERE id=?", (deal_id,))
    await cb.message.edit_reply_markup(None)
    # notify admin and user
    uid = (await db_exec("SELECT user_id FROM deals WHERE id=?", (deal_id,), True, True))[0]
    await bot.send_message(
        uid,
        f"✅ Ваша заявка #{deal_id} принята администратором. Ожидайте дальнейших инструкций.")
    await bot.send_message(
        ADMIN_ID,
        f"🟢 Сделка #{deal_id} принята и активна.",
        reply_markup=inline_kb([
            ("🏁 ЗАВЕРШИТЬ СДЕЛКУ", f"finish:{deal_id}")
        ])
    )
    await log_admin(cb.from_user.id, "accept_deal", str(deal_id))

@dp.callback_query(F.data.startswith("decline:"))
async def admin_decline(cb: CallbackQuery):
    deal_id = int(cb.data.split(":")[1])
    await cb.answer()
    await db_exec("UPDATE deals SET status='cancelled' WHERE id=?", (deal_id,))
    await cb.message.edit_reply_markup(None)
    uid = (await db_exec("SELECT user_id FROM deals WHERE id=?", (deal_id,), True, True))[0]
    await bot.send_message(uid, f"❌ Ваша заявка #{deal_id} отклонена администратором.")
    await bot.send_message(ADMIN_ID, f"❌ Сделка #{deal_id} отклонена.")

@dp.callback_query(F.data.startswith("finish:"))
async def finish_deal(cb: CallbackQuery):
    deal_id = int(cb.data.split(":")[1])
    await cb.answer()
    await db_exec("UPDATE deals SET status='done' WHERE id=? AND status='in_work'", (deal_id,))
    await cb.message.edit_reply_markup(None)
    uid = (await db_exec("SELECT user_id FROM deals WHERE id=?", (deal_id,), True, True))[0]
    await bot.send_message(uid, "🎉 Сделка завершена.")
    await bot.send_message(ADMIN_ID, f"🎉 Сделка #{deal_id} завершена.")

@dp.callback_query(F.data.startswith("user_cancel:"))
async def user_cancel(cb: CallbackQuery):
    deal_id = int(cb.data.split(":")[1])
    uid = cb.from_user.id
    await cb.answer()
    deal = await db_exec(
        "SELECT user_id,status FROM deals WHERE id=?",
        (deal_id,), True, True
    )
    if not deal:
        return
    if deal[0] != uid:
        return
    if deal[1] == "done":
        return
    await db_exec("UPDATE deals SET status='cancelled' WHERE id=?", (deal_id,))
    await cb.message.edit_reply_markup(None)
    await bot.send_message(uid, f"❌ Сделка #{deal_id} отменена.")
    await bot.send_message(ADMIN_ID, f"❌ Пользователь отменил сделку #{deal_id}.")

@dp.callback_query(F.data.startswith("cancel:"))
async def admin_cancel(cb: CallbackQuery):
    deal_id = int(cb.data.split(":")[1])
    await cb.answer()
    await db_exec("UPDATE deals SET status='cancelled' WHERE id=?", (deal_id,))
    await cb.message.edit_reply_markup(None)
    uid = (await db_exec("SELECT user_id FROM deals WHERE id=?", (deal_id,), True, True))[0]
    await bot.send_message(uid, f"❌ Администратор отменил сделку #{deal_id}.")
    await log_admin(cb.from_user.id, "cancel_deal", str(deal_id))



# ================== ADMIN PANEL ==================

@dp.message(F.text == "🛠 АДМИН ПАНЕЛЬ")
async def admin_panel(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer(
        "🛠 <b>АДМИН ПАНЕЛЬ</b>",
        reply_markup=reply_kb(
            "📊 СТАТИСТИКА",
            "📂 АКТИВНЫЕ СДЕЛКИ",
            "🚫 ЗАБАНЕННЫЕ",
            "📜 ЛОГИ СДЕЛОК",
            "⚠️ ФЛУДЕРЫ",
            "💱 НАСТРОЙКИ КУРСА",
            "⛔ ЗАБАНИТЬ",
            "♻️ РАЗБАНИТЬ",
            "⬅ ГЛАВНОЕ МЕНЮ"
        )
    )

@dp.message(F.text == "📊 СТАТИСТИКА")
async def admin_stats(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    total = (await db_exec("SELECT COUNT(*) FROM deals", fetch=True, one=True))[0]
    done = (await db_exec("SELECT COUNT(*) FROM deals WHERE status='done'", fetch=True, one=True))[0]
    active = (await db_exec(
        "SELECT COUNT(*) FROM deals WHERE status='in_work'",
        fetch=True, one=True
    ))[0]
    await msg.answer(
        "📊 <b>Статистика</b>\n"
        f"Всего сделок: <b>{total}</b>\n"
        f"Активных: <b>{active}</b>\n"
        f"Завершённых: <b>{done}</b>",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )

@dp.message(F.text == "📂 АКТИВНЫЕ СДЕЛКИ")
async def admin_active(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    rows = await db_exec(
        "SELECT id,user_id,amount_kk,currency,status FROM deals "
        "WHERE status='in_work' "
        "ORDER BY id DESC LIMIT 20",
        fetch=True
    )
    if not rows:
        return await msg.answer("📂 Активных сделок нет.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    for did, uid, kk, cur, st in rows:
        await msg.answer(
            f"📂 <b>#{did}</b> | UID {uid}\n"
            f"📦 {kk_fmt(kk)} | {sum_fmt(cur,kk)}\n"
            f"📌 <i>{st}</i>",
            reply_markup=inline_kb([
                ("🏁 ЗАВЕРШИТЬ СДЕЛКУ", f"finish:{did}"),
                ("❌ ОТМЕНИТЬ", f"cancel:{did}"),
                ("⛔ ЗАБАНИТЬ", f"admin_ban:{uid}")
            ])
        )

@dp.message(F.text == "🚫 ЗАБАНЕННЫЕ")
async def admin_banned(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    rows = await db_exec(
        "SELECT user_id,banned_until FROM users WHERE banned_until>?",
        (int(time.time()),),
        fetch=True
    )
    if not rows:
        return await msg.answer("🚫 Забаненных нет.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    text = "🚫 <b>Забаненные пользователи</b>\n\n"
    now = int(time.time())
    for uid, until in rows:
        mins = (until - now) // 60
        text += f"UID {uid} — {mins} мин.\n"
    await msg.answer(text, reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))





@dp.message(F.text == "💱 НАСТРОЙКИ КУРСА")
async def admin_rates(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer(
        "💱 <b>НАСТРОЙКА КУРСОВ И ЛИМИТОВ</b>",
        reply_markup=reply_kb(
            "UAH КУРС",
            "USDT КУРС",
            "UAH МИНИМУМ",
            "BEP20 МИНИМУМ",
            "TRC20 МИНИМУМ",
            "⬅ ГЛАВНОЕ МЕНЮ"
        )
    )
    await state.set_state(AdminRateFSM.choose)

@dp.message(AdminRateFSM.choose)
async def admin_rate_choose(msg: Message, state: FSMContext):
    mapping = {
        "UAH КУРС": ("RATE_UAH",),
        "USDT КУРС": ("RATE_USDT",),
        "UAH МИНИМУМ": ("UAH_MIN",),
        "BEP20 МИНИМУМ": ("USDT_BEP20_MIN",),
        "TRC20 МИНИМУМ": ("USDT_TRC20_MIN",),
    }
    if msg.text not in mapping:
        return
    await state.update_data(key=mapping[msg.text][0])
    await msg.answer("Введите новое значение:")
    await state.set_state(AdminRateFSM.edit_value)

@dp.message(AdminRateFSM.edit_value)
async def admin_rate_set(msg: Message, state: FSMContext):
    data = await state.get_data()
    key = data["key"]
    try:
        val = float(msg.text) if "RATE" in key else int(msg.text)
    except:
        await msg.answer("Неверное значение.")
        return

    global RATE_UAH, RATE_USDT
    if key == "RATE_UAH":
        RATE_UAH = val
        SERVER_RATES["R2 Rise"]["UAH"] = val
    elif key == "RATE_USDT":
        RATE_USDT = val
        SERVER_RATES["R2 Rise"]["USDT"] = val
    else:
        SERVER_LIMITS["R2 Rise"][key] = val

    await msg.answer("✅ Значение обновлено.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    await state.clear()

# ================== ADMIN BAN / UNBAN ==================



class AdminBanFSM(StatesGroup):
    ban_uid = State()
    ban_minutes = State()
    unban_uid = State()

@dp.message(F.text == "⛔ ЗАБАНИТЬ")
async def admin_ban_start(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer(
        "Введите UID пользователя для бана:",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )
    await state.set_state(AdminBanFSM.ban_uid)

@dp.message(AdminBanFSM.ban_uid)
async def admin_ban_uid(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("UID должен быть числом.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return
    await state.update_data(uid=int(msg.text))
    await msg.answer(
        "Введите время бана в минутах:",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )
    await state.set_state(AdminBanFSM.ban_minutes)

@dp.message(AdminBanFSM.ban_minutes)
async def admin_ban_minutes(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("Минуты должны быть числом.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return
    data = await state.get_data()
    uid = data["uid"]
    minutes = int(msg.text)
    until = int(time.time()) + minutes * 60

    await db_exec(
        "INSERT OR REPLACE INTO users (user_id,banned_until) VALUES (?,?)",
        (uid, until)
    )

    await msg.answer(
        f"⛔ Пользователь {uid} забанен на {minutes} минут.",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )
    await log_admin(msg.from_user.id, "ban_user", str(uid))
    try:
        await bot.send_message(uid, "⛔ Вы были заблокированы администратором.")
    except:
        pass
    await state.clear()

@dp.message(F.text == "♻️ РАЗБАНИТЬ")
async def admin_unban_start(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    await msg.answer(
        "Введите UID пользователя для разбана:",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )
    await state.set_state(AdminBanFSM.unban_uid)

@dp.message(AdminBanFSM.unban_uid)
async def admin_unban_uid(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("UID должен быть числом.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
        return
    uid = int(msg.text)

    await db_exec(
        "INSERT OR REPLACE INTO users (user_id,banned_until) VALUES (?,0)",
        (uid,)
    )

    await msg.answer(
        f"♻️ Пользователь {uid} разбанен.",
        reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ")
    )
    await log_admin(msg.from_user.id, "unban_user", str(uid))
    try:
        await bot.send_message(uid, "♻️ Вы были разблокированы администратором.")
    except:
        pass
    await state.clear()


# ================== ADMIN DEAL LOGS ==================

@dp.message(F.text == "📜 ЛОГИ СДЕЛОК")
async def admin_deal_logs(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    rows = await db_exec(
        "SELECT id,user_id,amount_kk,currency,status,created_at FROM deals "
        "ORDER BY id DESC LIMIT 20",
        fetch=True
    )
    if not rows:
        return await msg.answer("📜 Логов нет.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    text = "📜 <b>Последние сделки</b>\n\n"
    for did, uid, kk, cur, st, ts in rows:
        t = time.strftime("%d.%m %H:%M", time.localtime(ts))
        text += f"#{did} | UID {uid} | {kk_fmt(kk)} | {st} | {t}\n"
    await msg.answer(text, reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))

@dp.message(F.text == "⚠️ ФЛУДЕРЫ")
async def admin_flooders(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    rows = await db_exec(
        "SELECT user_id, COUNT(*) as c FROM deals "
        "WHERE status='cancelled' "
        "GROUP BY user_id HAVING c>=3 "
        "ORDER BY c DESC LIMIT 10",
        fetch=True
    )
    if not rows:
        return await msg.answer("⚠️ Флудеров не найдено.", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    text = "⚠️ <b>Потенциальные флудеры</b>\n\n"
    for uid, c in rows:
        await msg.answer(
            f"UID {uid} — отмен: {c}",
            reply_markup=inline_kb([
                ("⛔ ЗАБАНИТЬ", f"admin_ban:{uid}")
            ])
        )
    await msg.answer("⬅ Возврат в меню", reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))



# ================== INLINE ADMIN BAN ==================

@dp.callback_query(F.data.startswith("admin_ban:"))
async def inline_admin_ban(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("Нет доступа", show_alert=True)
        return
    uid = int(cb.data.split(":")[1])
    until = int(time.time()) + 60 * 60
    await db_exec(
        "INSERT OR REPLACE INTO users (user_id,banned_until) VALUES (?,?)",
        (uid, until)
    )
    await log_admin(cb.from_user.id, "inline_ban", str(uid))
    try:
        await bot.send_message(uid, "⛔ Вы были заблокированы администратором.")
    except:
        pass
    await cb.answer("Пользователь забанен на 60 минут", show_alert=True)


# ================== TIMER ==================




# ================== ERRORS ==================

@dp.errors()
async def errors_handler(exception: Exception):
    logging.error("Exception: %s", exception)
    traceback.print_exc()
    return True


# ================== PREVIEW FIX OVERRIDES ==================

@dp.callback_query(F.data == "deal_restart")
async def deal_restart_fix(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.clear()
    await cb.message.answer(
        "🔄 <b>Создание заявки начато заново</b>",
        reply_markup=reply_kb("💴 ПРОДАТЬ СЕРЕБРО В ГРН", "💵 ПРОДАТЬ СЕРЕБРО В USDT", "⬅ ГЛАВНОЕ МЕНЮ")
    )

@dp.callback_query(F.data == "deal_confirm")
async def deal_confirm_fix(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    data = await state.get_data()

    await db_exec(
        "INSERT INTO deals (user_id,currency,bank,initials,usdt_net,amount_kk,status,created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (
            cb.from_user.id,
            data.get("currency"),
            data.get("bank"),
            data.get("initials"),
            data.get("usdt_net"),
            data.get("amount"),
            "new",
            int(time.time())
        )
    )

    deal_id = (await db_exec("SELECT MAX(id) FROM deals", fetch=True, one=True))[0]

    user = cb.from_user
    username = f"@{user.username}" if user.username else f"id:{user.id}"

    admin_text = (
        f"🆕 <b>Заявка #{deal_id}</b>\n"
        f"👤 Пользователь: <b>{username}</b>\n"
        f"🖥 Сервер: <b>R2 Rise</b>\n"
        f"💱 Валюта: <b>{data.get('currency')}</b>\n"
    )

    if data.get("currency") == "UAH":
        admin_text += (
            f"🏦 Банк: <b>{data.get('bank')}</b>\n"
            f"✍️ Инициалы: <b>{data.get('initials')}</b>\n"
        )
    else:
        admin_text += f"🌐 USDT сеть: <b>{data.get('usdt_net')}</b>\n"

    admin_text += (
        f"📦 Количество: <b>{kk_fmt(data.get('amount'))}</b>\n"
        f"💰 Сумма: <b>{sum_fmt(data.get('currency'), data.get('amount'))}</b>"
    )

    await bot.send_message(
        ADMIN_ID,
        admin_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ", url=f"tg://user?id={cb.from_user.id}")],
            [InlineKeyboardButton(text="✅ ПРИНЯТЬ", callback_data=f"accept:{deal_id}")],
            [InlineKeyboardButton(text="❌ ОТКЛОНИТЬ", callback_data=f"decline:{deal_id}")]
        ])
    )

    await cb.message.answer(TEXT["deal_sent"], reply_markup=reply_kb("⬅ ГЛАВНОЕ МЕНЮ"))
    await state.clear()



# ================== GLOBAL RECOVERY BUTTON ==================

@dp.message(F.text.in_({"/menu", "МЕНЮ", "🏠 МЕНЮ"}))
async def force_menu(msg: Message):
    """
    Глобальная аварийная точка возврата меню.
    Работает всегда, даже если FSM сломан или клавиатура пропала.
    """
    try:
        await dp.storage.clear(key=msg.from_user.id)
    except:
        pass
    await menu(msg)

# Автовосстановление меню при любом неизвестном сообщении
@dp.message()
async def fallback_recover(msg: Message):
    """
    Если пользователь потерял кнопки — возвращаем главное меню.
    """
    await menu(msg)






# ================== MAIN ==================

async def cleanup_expired_listings():
    """Фоновая задача для удаления истекших объявлений каждый час"""
    while True:
        try:
            await remove_expired_listings()
            logging.info("Expired listings cleanup completed")
        except Exception as e:
            logging.error(f"Error cleaning up expired listings: {e}")
        
        # Проверяем каждый час
        await asyncio.sleep(3600)

async def main():
    await init_db()
    
    # Запустить фоновую задачу для очистки истекших объявлений
    cleanup_task = asyncio.create_task(cleanup_expired_listings())
    
    try:
        await dp.start_polling(bot)
    finally:
        cleanup_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())


# ================== VERSION ==================
# VERSION: 1.7.1
# CHANGELOG:
# 1.7.1
# ! FIXED: Кнопки "Создать" и "Отменить" больше не исчезают при редактировании цены
# + Добавлено новое состояние MarketFSM.edit_price для редактирования цены
# + Обработчик market_edit_price корректно обновляет цену и возвращает к предпросмотру
# + Кнопка "Назад" при редактировании цены теперь отменяет редактирование вместо отмены всего создания
# ~ Улучшена логика потока создания объявления
#
# 1.7.0
# + Полная реализация системы Рынка (Marketplace)
# + Иерархия категорий: Оружие (Ближнее/Дальнее), Экипировка, Аксессуары, Сферы
# + Функции просмотра товаров с фильтрацией по подкатегориям
# + Создание объявлений с лимитом 5 активных объявлений на пользователя
# + Управление объявлениями (активные, завершённые, отклонённые)
# + Избранные объявления
# + Профили продавцов с отображением UID для администраторов
# + Функции администратора: удаление объявлений, блокировка продавцов
# + Проверка статуса бана при доступе к рынку
# 
# 1.3.5
# ~ Updated UAH rate to 65 for R2 Rise
#

# 1.3.4
# ! Fixed R2 Market opening text (development message only)
# ! Prevented menu override on market open
# ~ Based on 1.3.2 logic
#

# 1.3.3
# + Added 'R2 Рынок' section to main menu
# + Added development description stub
# ~ Based strictly on 1.3.2
#

# 1.3.2
# + Currency rates are now server-bound (R2 Rise)
# + Prepared structure for multi-server rates
# ~ Monolith preserved
#

# 1.3.1
# + Added server selection step (R2 Rise) before deal creation
# ~ No architecture changes
#

# + Added monolith extension scaffold (registries, hooks, feature flags)
# + Added internal metrics placeholders for future patches
# ~ No architecture changes (single-file preserved)

# ================== MONOLITH EXTENSION CORE ==================

FEATURE_FLAGS = {
    "metrics": False,
    "audit": False,
    "future_roles": False,
}

MONOLITH_REGISTRY = {
    "hooks": {},       # event_name -> [callables]
    "services": {},    # name -> object
    "metrics": {},     # key -> int/float
}

def register_hook(event: str, func):
    MONOLITH_REGISTRY.setdefault("hooks", {}).setdefault(event, []).append(func)

async def emit_hook(event: str, *args, **kwargs):
    for fn in MONOLITH_REGISTRY.get("hooks", {}).get(event, []):
        try:
            res = fn(*args, **kwargs)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            logging.error("Hook error %s: %s", event, e)

def metric_inc(key: str, value: int = 1):
    MONOLITH_REGISTRY.setdefault("metrics", {})[key] = MONOLITH_REGISTRY["metrics"].get(key, 0) + value

# Example future hook points (not wired yet):
# await emit_hook("deal_created", deal_id=deal_id)
# metric_inc("deals_created")



@dp.callback_query(F.data.startswith("profile:"))
async def open_profile(cb: CallbackQuery):
    uid = int(cb.data.split(":")[1])
    await cb.answer()
    await cb.message.answer(
        "👤 Профиль пользователя:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="ОТКРЫТЬ ПРОФИЛЬ",
                    url=f"tg://user?id={uid}"
                )
            ]]
        )
    )


@dp.callback_query(F.data.startswith("decline:"))
async def admin_decline(cb: CallbackQuery):
    deal_id = int(cb.data.split(":")[1])
    await cb.answer()

    await db_exec("UPDATE deals SET status='in_work' WHERE id=?", (deal_id,))
    await cb.message.edit_reply_markup(None)

    uid = (await db_exec(
        "SELECT user_id FROM deals WHERE id=?",
        (deal_id,), True, True
    ))[0]

    await bot.send_message(uid, f"❌ Ваша заявка #{deal_id} отклонена администратором.")
    await bot.send_message(ADMIN_ID, f"❌ Сделка #{deal_id} отклонена.")

"""
Interactive Keyboards for Telegram Username Bot & Advanced Admin Dashboard
"""
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)


def main_menu_reply_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Persistent bottom navigation keyboard (with admin access if privileged)"""
    kb = [
        [
            KeyboardButton(text="🔍 Поиск юзернейма"),
            KeyboardButton(text="👤 Мой профиль")
        ],
        [
            KeyboardButton(text="💎 Купить Премиум"),
            KeyboardButton(text="ℹ️ О сервисе")
        ]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="⚙️ Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)


def length_choice_inline_keyboard() -> InlineKeyboardMarkup:
    """Choose username length (5 or 6 characters)"""
    kb = [
        [
            InlineKeyboardButton(text="⚡ 5 символов (Редкие)", callback_data="search_len_5"),
            InlineKeyboardButton(text="✨ 6 символов (Красивые)", callback_data="search_len_6")
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="open_profile"),
            InlineKeyboardButton(text="💎 Безлимит Премиум", callback_data="open_premium")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def username_result_inline_keyboard(username: str, length: int) -> InlineKeyboardMarkup:
    """Actions after username is found"""
    kb = [
        [
            InlineKeyboardButton(text=f"🔗 Занять @{username}", url=f"https://t.me/{username}")
        ],
        [
            InlineKeyboardButton(text=f"🔄 Искать ещё ({length} симв.)", callback_data=f"search_len_{length}"),
            InlineKeyboardButton(text="🔍 Другая длина", callback_data="menu_search")
        ],
        [
            InlineKeyboardButton(text="👤 В профиль", callback_data="open_profile"),
            InlineKeyboardButton(text="💎 Премиум", callback_data="open_premium")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def profile_inline_keyboard(is_premium: bool = False) -> InlineKeyboardMarkup:
    """Actions inside user profile"""
    kb = []
    if not is_premium:
        kb.append([
            InlineKeyboardButton(text="💎 Купить Премиум (Безлимит)", callback_data="open_premium")
        ])
    kb.append([
        InlineKeyboardButton(text="🔍 Начать поиск", callback_data="menu_search"),
        InlineKeyboardButton(text="🎟 Ввести промокод", callback_data="enter_promocode")
    ])
    kb.append([
        InlineKeyboardButton(text="📜 Последние находки", callback_data="view_history"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="open_profile")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def premium_offer_inline_keyboard() -> InlineKeyboardMarkup:
    """Premium purchase options and promo activation"""
    kb = [
        [
            InlineKeyboardButton(text="⚡ Тестовый Премиум (1 клик)", callback_data="activate_demo_premium")
        ],
        [
            InlineKeyboardButton(text="🎟 Активировать промокод", callback_data="enter_promocode")
        ],
        [
            InlineKeyboardButton(text="🔍 Поиск юзернеймов", callback_data="menu_search"),
            InlineKeyboardButton(text="👤 В профиль", callback_data="open_profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def no_queries_left_inline_keyboard() -> InlineKeyboardMarkup:
    """Shown when a free user exhausts their 2 queries"""
    kb = [
        [
            InlineKeyboardButton(text="💎 Снять лимит (Премиум)", callback_data="open_premium"),
            InlineKeyboardButton(text="🎟 Промокод", callback_data="enter_promocode")
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="open_profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# --------------------------------------------------------------------------
# Admin Panel Keyboards
# --------------------------------------------------------------------------

def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Control dashboard for administrators"""
    kb = [
        [
            InlineKeyboardButton(text="📊 Аналитика и статистика", callback_data="adm_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="adm_users_page_1")
        ],
        [
            InlineKeyboardButton(text="🔎 Найти пользователя", callback_data="adm_search_user"),
            InlineKeyboardButton(text="📢 Рассылка всем", callback_data="adm_broadcast")
        ],
        [
            InlineKeyboardButton(text="🎟 Промокоды", callback_data="adm_promos"),
            InlineKeyboardButton(text="💾 Скачать БД (.sqlite)", callback_data="adm_dump_db")
        ],
        [
            InlineKeyboardButton(text="❌ Закрыть панель", callback_data="adm_close")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_users_pagination_keyboard(users: list, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """List of users with pagination and quick inspection"""
    kb = []
    for u in users:
        badge = "🚫" if u.get("is_banned") else ("⭐️" if u.get("is_premium") else "👤")
        name = u.get("full_name") or f"ID {u['user_id']}"
        username_str = f"@{u['username']}" if u.get("username") else f"ID: {u['user_id']}"
        btn_text = f"{badge} {name[:14]} ({username_str[:12]})"
        kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"adm_u_{u['user_id']}")])

    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"adm_users_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"Стр. {current_page}/{total_pages}", callback_data="noop"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"adm_users_page_{current_page + 1}"))

    kb.append(nav_row)
    kb.append([
        InlineKeyboardButton(text="🔎 Поиск по ID/юзеру", callback_data="adm_search_user"),
        InlineKeyboardButton(text="🔙 В админку", callback_data="adm_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_user_management_keyboard(target_id: int, is_banned: bool, is_premium: bool) -> InlineKeyboardMarkup:
    """Comprehensive user management options: ban/unban, premium, bonus queries"""
    ban_btn_text = "🟢 Разбанить пользователя" if is_banned else "🚫 Забанить пользователя"
    ban_cb = f"adm_action_unban_{target_id}" if is_banned else f"adm_action_ban_{target_id}"

    prem_btn_text = "❌ Забрать Премиум" if is_premium else "⭐️ Выдать Премиум (Безлимит)"
    prem_cb = f"adm_action_unprem_{target_id}" if is_premium else f"adm_action_prem_{target_id}"

    kb = [
        [InlineKeyboardButton(text=ban_btn_text, callback_data=ban_cb)],
        [InlineKeyboardButton(text=prem_btn_text, callback_data=prem_cb)],
        [
            InlineKeyboardButton(text="➕ +5 поисков", callback_data=f"adm_action_add5_{target_id}"),
            InlineKeyboardButton(text="➕ +20 поисков", callback_data=f"adm_action_add20_{target_id}")
        ],
        [
            InlineKeyboardButton(text="📜 Находки пользователя", callback_data=f"adm_user_history_{target_id}")
        ],
        [
            InlineKeyboardButton(text="👥 К списку пользователей", callback_data="adm_users_page_1"),
            InlineKeyboardButton(text="🔙 В админку", callback_data="adm_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="🚀 Отправить рассылку сейчас", callback_data="adm_broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="adm_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_promocodes_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="adm_new_promo")],
        [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="adm_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

"""
Interactive Keyboards for Telegram Username Bot & Advanced Admin Dashboard
Features native Telegram colored buttons (green: success, purple/primary: primary)
and luxury VIP emoji styling.
"""
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)


def main_menu_reply_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Persistent bottom navigation keyboard with premium emojis"""
    kb = [
        [
            KeyboardButton(text="🔍 Проверить юзернейм (ввести свой)"),
        ],
        [
            KeyboardButton(text="⚡ Свободный юз (5 симв.)"),
            KeyboardButton(text="✨ Свободный юз (6 симв.)")
        ],
        [
            KeyboardButton(text="👤 Мой профиль"),
            KeyboardButton(text="💎 Купить Премиум")
        ],
        [
            KeyboardButton(text="📜 Меню и тарифы")
        ]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="⚙️ Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)


def welcome_agreement_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Agreement & Navigation Screen matching user design mockup:
    - Row 1: 📜 Соглашение | 🔒 Конфиденциальность
    - Row 2: 💳 Тарифы и цены | 🆘 Поддержка
    - Row 3: 🧩 Что умеет бот
    - Row 4: Distributed 2 colored buttons:
             🟢 Зеленая: ✅ Принять и запустить (style="success")
             🟣 Фиолетовая: 💎 Премиум доступ (style="primary")
    """
    kb = [
        [
            InlineKeyboardButton(text="📜 Соглашение", callback_data="info_agreement"),
            InlineKeyboardButton(text="🔒 Конфиденциальность", callback_data="info_privacy")
        ],
        [
            InlineKeyboardButton(text="💳 Тарифы и цены", callback_data="info_pricing"),
            InlineKeyboardButton(text="🆘 Поддержка", callback_data="info_support")
        ],
        [
            InlineKeyboardButton(text="🧩 Что умеет бот", callback_data="info_features")
        ],
        [
            InlineKeyboardButton(text="✅ Принять и запустить", callback_data="start_flow", style="success"),
            InlineKeyboardButton(text="💎 Премиум доступ", callback_data="open_premium", style="primary")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def info_modal_back_keyboard() -> InlineKeyboardMarkup:
    """Back button with quick action triggers"""
    kb = [
        [
            InlineKeyboardButton(text="✅ Начать поиск", callback_data="search_len_5", style="success"),
            InlineKeyboardButton(text="💎 Премиум доступ", callback_data="open_premium", style="primary")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в меню сервиса", callback_data="open_service_info")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def username_check_result_inline_keyboard(username: str, is_free: bool, status_type: str) -> InlineKeyboardMarkup:
    """Action buttons with Green & Purple styles based on handle status"""
    kb = []
    if is_free:
        kb.append([
            InlineKeyboardButton(text=f"✅ Занять @{username} в Telegram", url=f"https://t.me/{username}", style="success"),
            InlineKeyboardButton(text="💎 Снять лимит (Безлимит)", callback_data="open_premium", style="primary")
        ])
        kb.append([
            InlineKeyboardButton(text="🔄 Найти ещё (5 симв.)", callback_data="search_len_5"),
            InlineKeyboardButton(text="🔄 Найти ещё (6 симв.)", callback_data="search_len_6")
        ])
    elif status_type == "FRAGMENT":
        kb.append([
            InlineKeyboardButton(text=f"💎 Открыть лот на Fragment", url=f"https://fragment.com/username/{username}", style="success"),
            InlineKeyboardButton(text="⚡ Найти бесплатный аналог", callback_data="search_len_5", style="primary")
        ])
    else:
        kb.append([
            InlineKeyboardButton(text="⚡ Найти свободный юзернейм", callback_data="search_len_5", style="success"),
            InlineKeyboardButton(text="💎 Купить Премиум", callback_data="open_premium", style="primary")
        ])
        kb.append([
            InlineKeyboardButton(text=f"👤 Открыть профиль @{username}", url=f"https://t.me/{username}")
        ])

    kb.append([
        InlineKeyboardButton(text="🔍 Проверить другой юзернейм", callback_data="prompt_check_custom"),
        InlineKeyboardButton(text="👤 Мой профиль", callback_data="open_profile")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def free_found_inline_keyboard(username: str, length: int) -> InlineKeyboardMarkup:
    """Actions after free username is found: 2 colored primary actions"""
    next_len = 6 if length == 5 else 5
    kb = [
        [
            InlineKeyboardButton(text=f"✅ Занять @{username} прямо сейчас", url=f"https://t.me/{username}", style="success"),
            InlineKeyboardButton(text="💎 Оформить Безлимит", callback_data="open_premium", style="primary")
        ],
        [
            InlineKeyboardButton(text=f"🔄 Найти ещё ({length} симв.)", callback_data=f"search_len_{length}"),
            InlineKeyboardButton(text=f"✨ Найти ({next_len} симв.)", callback_data=f"search_len_{next_len}")
        ],
        [
            InlineKeyboardButton(text="🔍 Проверить свой", callback_data="prompt_check_custom"),
            InlineKeyboardButton(text="👤 В профиль", callback_data="open_profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def profile_inline_keyboard(is_premium: bool = False) -> InlineKeyboardMarkup:
    """Actions inside user profile with green & purple colored buttons"""
    kb = []
    if not is_premium:
        kb.append([
            InlineKeyboardButton(text="💎 Купить Премиум (Безлимит)", callback_data="open_premium", style="primary"),
            InlineKeyboardButton(text="⚡ Найти свободный юз", callback_data="search_len_5", style="success")
        ])
    else:
        kb.append([
            InlineKeyboardButton(text="⚡ Свободный юз (5 симв.)", callback_data="search_len_5", style="success"),
            InlineKeyboardButton(text="✨ Свободный юз (6 симв.)", callback_data="search_len_6", style="primary")
        ])

    kb.append([
        InlineKeyboardButton(text="🔍 Проверить юзернейм", callback_data="prompt_check_custom"),
        InlineKeyboardButton(text="🎟 Ввести промокод", callback_data="enter_promocode")
    ])
    kb.append([
        InlineKeyboardButton(text="📜 История проверок", callback_data="view_history"),
        InlineKeyboardButton(text="🔄 Обновить профиль", callback_data="open_profile")
    ])
    kb.append([
        InlineKeyboardButton(text="ℹ️ Меню сервиса и тарифы", callback_data="open_service_info")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def premium_offer_inline_keyboard() -> InlineKeyboardMarkup:
    """Premium purchase options with Green & Purple colored buttons"""
    kb = [
        [
            InlineKeyboardButton(text="⚡ Тестовый Премиум (1 клик)", callback_data="activate_demo_premium", style="primary"),
            InlineKeyboardButton(text="🎟 Ввести промокод", callback_data="enter_promocode", style="success")
        ],
        [
            InlineKeyboardButton(text="🔍 Проверить юзернейм", callback_data="prompt_check_custom"),
            InlineKeyboardButton(text="👤 В профиль", callback_data="open_profile")
        ],
        [
            InlineKeyboardButton(text="💳 Подробнее о тарифах", callback_data="info_pricing")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def no_queries_left_inline_keyboard() -> InlineKeyboardMarkup:
    """Shown when a free user exhausts their queries: green & purple buttons"""
    kb = [
        [
            InlineKeyboardButton(text="💎 Снять лимит (Премиум)", callback_data="open_premium", style="primary"),
            InlineKeyboardButton(text="🎟 Ввести промокод", callback_data="enter_promocode", style="success")
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="open_profile"),
            InlineKeyboardButton(text="💳 Тарифы", callback_data="info_pricing")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# --------------------------------------------------------------------------
# Admin Panel Keyboards
# --------------------------------------------------------------------------

def admin_main_keyboard() -> InlineKeyboardMarkup:
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
    kb = []
    for u in users:
        badge = "⭐️" if u["is_premium"] else "⚡"
        ban_mark = "🚫 " if u["is_banned"] else ""
        name = u["full_name"][:14]
        tag = f"@{u['username']}" if u["username"] else f"ID:{u['user_id']}"
        kb.append([
            InlineKeyboardButton(
                text=f"{ban_mark}{badge} {name} ({tag})", 
                callback_data=f"adm_u_{u['user_id']}"
            )
        ])

    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"adm_users_page_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"Стр. {current_page} / {max(1, total_pages)}", callback_data="noop"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"adm_users_page_{current_page + 1}"))

    if nav_row:
        kb.append(nav_row)

    kb.append([InlineKeyboardButton(text="🔙 В админ-меню", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_user_management_keyboard(target_id: int, is_banned: bool, is_premium: bool) -> InlineKeyboardMarkup:
    kb = []
    row1 = []
    if is_banned:
        row1.append(InlineKeyboardButton(text="🟢 Разбанить", callback_data=f"adm_action_unban_{target_id}", style="success"))
    else:
        row1.append(InlineKeyboardButton(text="🚫 Забанить", callback_data=f"adm_action_ban_{target_id}", style="danger"))

    if is_premium:
        row1.append(InlineKeyboardButton(text="❌ Снять Премиум", callback_data=f"adm_action_unprem_{target_id}"))
    else:
        row1.append(InlineKeyboardButton(text="⭐️ Выдать Премиум", callback_data=f"adm_action_prem_{target_id}", style="primary"))
    kb.append(row1)

    kb.append([
        InlineKeyboardButton(text="➕ Начислить 5 проверок", callback_data=f"adm_action_add5_{target_id}"),
        InlineKeyboardButton(text="➕ Начислить 20 проверок", callback_data=f"adm_action_add20_{target_id}")
    ])
    kb.append([
        InlineKeyboardButton(text="📜 История находок", callback_data=f"adm_user_history_{target_id}"),
        InlineKeyboardButton(text="👥 К списку", callback_data="adm_users_page_1")
    ])
    kb.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="🚀 Да, начать рассылку", callback_data="adm_broadcast_confirm", style="success"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="adm_main", style="danger")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_promocodes_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="➕ Создать новый промокод", callback_data="adm_new_promo", style="success")
        ],
        [
            InlineKeyboardButton(text="🔙 В админ-меню", callback_data="adm_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

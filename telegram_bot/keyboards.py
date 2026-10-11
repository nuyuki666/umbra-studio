"""
Interactive Inline and Reply Keyboards for Telegram Username Bot
"""
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)


def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """Persistent bottom navigation keyboard"""
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

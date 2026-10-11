"""
Interactive keyboards for Mod_SaveBot: Help menus, Games (TTT, BW, Duel)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def get_help_main_keyboard() -> InlineKeyboardMarkup:
    """Main category selector matching @Mod_SaveBot layout"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▫️ Сообщения", callback_data="help_cat_messages"),
            InlineKeyboardButton(text="▫️ Форматирование", callback_data="help_cat_formatting")
        ],
        [
            InlineKeyboardButton(text="▫️ Игры", callback_data="help_cat_games"),
            InlineKeyboardButton(text="▫️ Обработка", callback_data="help_cat_processing")
        ],
        [
            InlineKeyboardButton(text="▫️ Остальное", callback_data="help_cat_misc")
        ],
        [
            InlineKeyboardButton(text="✨ Полный список всех команд", callback_data="help_cat_all")
        ]
    ])


def get_help_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад в меню категорий", callback_data="help_cat_main")
        ]
    ])


def get_duel_keyboard(duel_id: str, bet: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"⚔️ Принять вызов ({bet} ⭐)", callback_data=f"duel_acc_{duel_id}"),
            InlineKeyboardButton(text="🏳️ Отклонить", callback_data=f"duel_dec_{duel_id}")
        ]
    ])


def get_ttt_board_keyboard(board: List[str], game_id: str) -> InlineKeyboardMarkup:
    """Generates 3x3 Tic-Tac-Toe inline keyboard"""
    kb = []
    symbols = {"-": "⬜", "X": "❌", "O": "⭕"}
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            cell = board[idx]
            text = symbols.get(cell, "⬜")
            cb = f"ttt_{game_id}_{idx}" if cell == "-" else f"ttt_noop_{game_id}"
            row.append(InlineKeyboardButton(text=text, callback_data=cb))
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_bw_board_keyboard(board: List[str], game_id: str) -> InlineKeyboardMarkup:
    """Generates 3x3 'Закрась поле' (Black & White grid) inline keyboard"""
    kb = []
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            color = board[idx]
            # 🟦 Blue / 🟩 Green / ⬜ Empty
            icon = "⬜" if color == "E" else ("🟦" if color == "B" else "🟩")
            row.append(InlineKeyboardButton(text=icon, callback_data=f"bw_{game_id}_{idx}"))
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)

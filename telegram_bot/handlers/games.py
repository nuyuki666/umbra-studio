"""
Handlers for "Игры":
.bw, .dice, .duel, .flip, .chk, .ttt
"""
import asyncio
import random
import uuid
from typing import Dict, Any, List, Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import database as db
from keyboards import get_ttt_board_keyboard, get_bw_board_keyboard, get_duel_keyboard

router = Router(name="games_router")

# Active game memory states
ACTIVE_TTT: Dict[str, Dict[str, Any]] = {}
ACTIVE_BW: Dict[str, Dict[str, Any]] = {}
ACTIVE_DUELS: Dict[str, Dict[str, Any]] = {}


def check_ttt_winner(board: List[str]) -> Optional[str]:
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
        (0, 4, 8), (2, 4, 6)             # diags
    ]
    for a, b, c in lines:
        if board[a] != "-" and board[a] == board[b] == board[c]:
            return board[a]
    if "-" not in board:
        return "DRAW"
    return None


# --------------------------------------------------------------------------
# 1. .flip — подбросить монетку
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]flip"))
async def cmd_flip(message: Message):
    status_msg = await message.answer("🪙 Монетка подбрасывается...")
    await asyncio.sleep(0.6)
    res = random.choice(["Орёл 🦅", "Решка 🪙"])
    await status_msg.edit_text(f"🎲 <b>Результат броска:</b>\n\nВыпало: <b>{res}</b>!", parse_mode="HTML")


# --------------------------------------------------------------------------
# 2. .dice — в кубик на звезды
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]dice"))
async def cmd_dice(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = db.get_or_create_user(user_id, message.from_user.username, message.from_user.full_name)

    parts = message.text.strip().split()
    bet = 10
    if len(parts) > 1 and parts[1].isdigit():
        bet = max(1, min(1000, int(parts[1])))

    if user["stars"] < bet:
        await message.answer(
            f"❌ Недостаточно звёзд для ставки! Баланс: <b>{user['stars']} ⭐</b>, ставка: <b>{bet} ⭐</b>.",
            parse_mode="HTML"
        )
        return

    db.update_stars(user_id, -bet)

    await message.answer(f"🎲 <b>Бросок кубика на {bet} ⭐!</b>\nЕсли выпадет 4, 5 или 6 — победа 2x!", parse_mode="HTML")
    dice_msg = await bot.send_dice(message.chat.id, emoji="🎲")
    dice_val = dice_msg.dice.value

    await asyncio.sleep(3.5)
    if dice_val >= 4:
        win_amount = bet * 2
        new_bal = db.update_stars(user_id, win_amount)
        await message.answer(
            f"🎉 <b>ПОБЕДА!</b> Выпало <b>{dice_val}</b>.\n"
            f"Вы выиграли: <b>+{win_amount} ⭐</b>! Баланс: <b>{new_bal} ⭐</b>",
            parse_mode="HTML"
        )
    else:
        new_bal = db.get_or_create_user(user_id)["stars"]
        await message.answer(
            f"😢 <b>Проигрыш...</b> Выпало <b>{dice_val}</b>.\n"
            f"Списано: <b>-{bet} ⭐</b>. Баланс: <b>{new_bal} ⭐</b>",
            parse_mode="HTML"
        )


# --------------------------------------------------------------------------
# 3. .duel — дуэль на звёзды
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]duel"))
async def cmd_duel(message: Message):
    if not message.reply_to_message:
        await message.answer("⚠️ Ответьте командой <code>.duel [ставка]</code> на сообщение противника!", parse_mode="HTML")
        return

    challenger = message.from_user
    opponent = message.reply_to_message.from_user

    if challenger.id == opponent.id:
        await message.answer("❌ Нельзя стреляться с самим собой!")
        return

    parts = message.text.strip().split()
    bet = 20
    if len(parts) > 1 and parts[1].isdigit():
        bet = max(5, min(500, int(parts[1])))

    u_chal = db.get_or_create_user(challenger.id, challenger.username, challenger.full_name)
    u_opp = db.get_or_create_user(opponent.id, opponent.username, opponent.full_name)

    if u_chal["stars"] < bet:
        await message.answer(f"❌ У вас недостаточно звёзд! Баланс: {u_chal['stars']} ⭐")
        return
    if u_opp["stars"] < bet:
        await message.answer(f"❌ У противника недостаточно звёзд! Баланс: {u_opp['stars']} ⭐")
        return

    duel_id = str(uuid.uuid4())[:8]
    ACTIVE_DUELS[duel_id] = {
        "challenger_id": challenger.id,
        "challenger_name": challenger.full_name,
        "opponent_id": opponent.id,
        "opponent_name": opponent.full_name,
        "bet": bet
    }

    text = (
        f"⚔️ <b>ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
        f"Игрок {challenger.mention_html()} вызывает {opponent.mention_html()} на дуэль!\n"
        f"💰 Ставка с каждого: <b>{bet} ⭐</b> (банк: <b>{bet*2} ⭐</b>)\n\n"
        f"{opponent.mention_html()}, примете ли вы вызов?"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_duel_keyboard(duel_id, bet))


@router.callback_query(F.data.startswith("duel_acc_"))
async def cb_duel_accept(callback: CallbackQuery):
    duel_id = callback.data.split("_")[-1]
    duel = ACTIVE_DUELS.get(duel_id)

    if not duel:
        await callback.answer("Дуэль устарела или уже завершена.", show_alert=True)
        return

    if callback.from_user.id != duel["opponent_id"]:
        await callback.answer("Этот вызов предназначен не вам!", show_alert=True)
        return

    await callback.answer("Вызов принят! Стрельба...")
    bet = duel["bet"]
    ch_id = duel["challenger_id"]
    op_id = duel["opponent_id"]

    db.update_stars(ch_id, -bet)
    db.update_stars(op_id, -bet)

    bank = bet * 2
    # Determine winner
    winner_id = random.choice([ch_id, op_id])
    loser_id = op_id if winner_id == ch_id else ch_id
    winner_name = duel["challenger_name"] if winner_id == ch_id else duel["opponent_name"]
    loser_name = duel["opponent_name"] if winner_id == ch_id else duel["challenger_name"]

    db.update_stars(winner_id, bank)
    db.update_game_win(winner_id, loser_id)
    del ACTIVE_DUELS[duel_id]

    text = (
        f"🔫 <b>ДУЭЛЬ СОСТОЯЛАСЬ!</b>\n\n"
        f"💥 Раздался выстрел...\n"
        f"Пуля просвистела, и <b>{loser_name}</b> падает на землю!\n\n"
        f"🏆 Победитель: <b>{winner_name}</b>!\n"
        f"💰 Выигрыш: <b>+{bank} ⭐</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("duel_dec_"))
async def cb_duel_decline(callback: CallbackQuery):
    duel_id = callback.data.split("_")[-1]
    duel = ACTIVE_DUELS.get(duel_id)
    if not duel:
        await callback.answer("Дуэль завершена.")
        return

    if callback.from_user.id not in [duel["opponent_id"], duel["challenger_id"]]:
        await callback.answer("Вы не участник дуэли.")
        return

    del ACTIVE_DUELS[duel_id]
    await callback.message.edit_text("🏳️ <b>Вызов на дуэль был отклонен.</b>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 4. .ttt — Крестики-нолики
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]ttt"))
async def cmd_ttt(message: Message):
    game_id = str(uuid.uuid4())[:8]
    p1 = message.from_user
    p2 = message.reply_to_message.from_user if message.reply_to_message else None

    ACTIVE_TTT[game_id] = {
        "board": ["-"] * 9,
        "p1_id": p1.id,
        "p1_name": p1.full_name,
        "p2_id": p2.id if p2 else None,
        "p2_name": p2.full_name if p2 else "Любой соперник / Бот",
        "turn": "X"  # X moves first
    }

    text = (
        f"❌⭕ <b>ИГРА: КРЕСТИКИ-НОЛИКИ</b>\n\n"
        f"• ❌ (Крестики): <b>{p1.full_name}</b>\n"
        f"• ⭕ (Нолики): <b>{ACTIVE_TTT[game_id]['p2_name']}</b>\n\n"
        f"👉 Ход: <b>❌ ({p1.full_name})</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_ttt_board_keyboard(ACTIVE_TTT[game_id]["board"], game_id))


@router.callback_query(F.data.startswith("ttt_"))
async def cb_ttt_move(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 3 or parts[1] == "noop":
        await callback.answer()
        return

    game_id = parts[1]
    idx = int(parts[2])
    game = ACTIVE_TTT.get(game_id)

    if not game:
        await callback.answer("Игра завершена.", show_alert=True)
        return

    u_id = callback.from_user.id

    # Register opponent if open game
    if game["p2_id"] is None and u_id != game["p1_id"]:
        game["p2_id"] = u_id
        game["p2_name"] = callback.from_user.full_name

    # Check turn
    current_sym = game["turn"]
    allowed_id = game["p1_id"] if current_sym == "X" else game["p2_id"]

    if allowed_id and u_id != allowed_id:
        await callback.answer("Сейчас не ваш ход!", show_alert=True)
        return

    # Make move
    game["board"][idx] = current_sym
    winner = check_ttt_winner(game["board"])

    if winner:
        if winner == "DRAW":
            res_text = "🤝 <b>Ничья! Победила дружба!</b>"
        else:
            w_name = game["p1_name"] if winner == "X" else game["p2_name"]
            res_text = f"🎉 <b>Победа игрока {w_name} ({winner})!</b>"

        await callback.message.edit_text(
            f"❌⭕ <b>ИГРА ОКОНЧЕНА!</b>\n\n{res_text}",
            parse_mode="HTML",
            reply_markup=get_ttt_board_keyboard(game["board"], game_id)
        )
        del ACTIVE_TTT[game_id]
        return

    # Toggle turn
    game["turn"] = "O" if current_sym == "X" else "X"
    next_name = game["p2_name"] if game["turn"] == "O" else game["p1_name"]

    text = (
        f"❌⭕ <b>ИГРА: КРЕСТИКИ-НОЛИКИ</b>\n\n"
        f"• ❌: <b>{game['p1_name']}</b>\n"
        f"• ⭕: <b>{game['p2_name']}</b>\n\n"
        f"👉 Ход: <b>{'❌' if game['turn']=='X' else '⭕'} ({next_name})</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_ttt_board_keyboard(game["board"], game_id))


# --------------------------------------------------------------------------
# 5. .bw — игра 'Закрась поле'
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]bw"))
async def cmd_bw(message: Message):
    game_id = str(uuid.uuid4())[:8]
    p1 = message.from_user
    ACTIVE_BW[game_id] = {
        "board": ["E"] * 9,
        "p1_id": p1.id,
        "p1_name": p1.full_name,
        "p2_id": None,
        "p2_name": "Соперник",
        "turn": "B"  # B = Blue, G = Green
    }
    text = (
        f"🎨 <b>ИГРА: ЗАКРАСЬ ПОЛЕ (3x3)</b>\n\n"
        f"• 🟦 Игрок 1: <b>{p1.full_name}</b>\n"
        f"• 🟩 Игрок 2: <b>Ожидание соперника...</b>\n\n"
        "Кто закрасит больше клеток своего цвета, тот и победил!\n"
        f"👉 Ход: <b>🟦 ({p1.full_name})</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_bw_board_keyboard(ACTIVE_BW[game_id]["board"], game_id))


@router.callback_query(F.data.startswith("bw_"))
async def cb_bw_move(callback: CallbackQuery):
    parts = callback.data.split("_")
    game_id = parts[1]
    idx = int(parts[2])
    game = ACTIVE_BW.get(game_id)

    if not game:
        await callback.answer("Игра завершена.", show_alert=True)
        return

    u_id = callback.from_user.id
    if game["p2_id"] is None and u_id != game["p1_id"]:
        game["p2_id"] = u_id
        game["p2_name"] = callback.from_user.full_name

    cur_turn = game["turn"]
    allowed_id = game["p1_id"] if cur_turn == "B" else game["p2_id"]

    if allowed_id and u_id != allowed_id:
        await callback.answer("Сейчас не ваш ход!", show_alert=True)
        return

    game["board"][idx] = cur_turn

    # Check if all cells filled
    if "E" not in game["board"]:
        b_count = game["board"].count("B")
        g_count = game["board"].count("G")
        if b_count > g_count:
            w_text = f"🏆 Победил 🟦 <b>{game['p1_name']}</b> со счётом {b_count}:{g_count}!"
        elif g_count > b_count:
            w_text = f"🏆 Победил 🟩 <b>{game['p2_name']}</b> со счётом {g_count}:{b_count}!"
        else:
            w_text = f"🤝 <b>Ничья!</b> Равное количество клеток ({b_count}:{g_count})."

        await callback.message.edit_text(
            f"🎨 <b>ИГРА ЗАВЕРШЕНА!</b>\n\n{w_text}",
            parse_mode="HTML",
            reply_markup=get_bw_board_keyboard(game["board"], game_id)
        )
        del ACTIVE_BW[game_id]
        return

    game["turn"] = "G" if cur_turn == "B" else "B"
    next_name = game["p2_name"] if game["turn"] == "G" else game["p1_name"]

    text = (
        f"🎨 <b>ИГРА: ЗАКРАСЬ ПОЛЕ (3x3)</b>\n\n"
        f"• 🟦: <b>{game['p1_name']}</b> ({game['board'].count('B')})\n"
        f"• 🟩: <b>{game['p2_name']}</b> ({game['board'].count('G')})\n\n"
        f"👉 Ход: <b>{'🟦' if game['turn']=='B' else '🟩'} ({next_name})</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_bw_board_keyboard(game["board"], game_id))


# --------------------------------------------------------------------------
# 6. .chk — шашки
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]chk"))
async def cmd_chk(message: Message):
    board = (
        "🏁 <b>МИНИ-ШАШКИ (CHANCE BOARD)</b>\n\n"
        "8 ⬛⚪⬛⚪⬛⚪⬛⚪\n"
        "7 ⚪⬛⚪⬛⚪⬛⚪⬛\n"
        "6 ⬛⚪⬛⚪⬛⚪⬛⚪\n"
        "5 ⬛⬛⬛⬛⬛⬛⬛⬛\n"
        "4 ⬛⬛⬛⬛⬛⬛⬛⬛\n"
        "3 ⚫⬛⚫⬛⚫⬛⚫⬛\n"
        "2 ⬛⚫⬛⚫⬛⚫⬛⚫\n"
        "1 ⚫⬛⚫⬛⚫⬛⚫⬛\n"
        "  A B C D E F G H\n\n"
        "👉 Ход белых: <code>C3 → D4</code>\n"
        "Используйте ответ на это сообщение для фиксации хода!"
    )
    await message.answer(board, parse_mode="HTML")

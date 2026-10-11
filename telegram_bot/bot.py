"""
Mod_SaveBot Clone — Main Telegram Bot Entry Point
Supports all userbot-like commands starting with . and /
"""
import asyncio
import logging
import sys
import os

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import BOT_TOKEN, ADMIN_IDS
import database as db
from handlers.messages import router as messages_router
from handlers.formatting import router as formatting_router
from handlers.games import router as games_router
from handlers.processing import router as processing_router
from handlers.misc import router as misc_router
from keyboards import get_help_main_keyboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mod_save_bot")

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)


# --------------------------------------------------------------------------
# 1. /start Greeting Handler
# --------------------------------------------------------------------------
@dp.message(CommandStart())
async def handle_start(message: Message):
    user = message.from_user
    db.get_or_create_user(user.id, user.username, user.full_name)

    text = (
        f"👋 <b>Привет, {user.full_name}!</b>\n\n"
        "⚡ <b>Mod_SaveBot Core</b> — универсальный многофункциональный бот с набором команд:\n\n"
        "▫️ <b>Работа с сообщениями</b> (.check, .spam, .love, .mute, .sw, .troll, .type, .zaebu)\n"
        "▫️ <b>Форматирование</b> (.bold, .italic, .monospace, .underline, .leet, .kawaii, .tsundere, .yandere)\n"
        "▫️ <b>Мини-игры</b> (.bw, .dice, .duel, .flip, .chk, .ttt)\n"
        "▫️ <b>Обработка профиля & медиа</b> (.clone, .dox, .doxp, .fv, .afk, .autoresponder, .gifts, .info, .nk, .short, .status, .story, .time, .yars, .gif)\n"
        "▫️ <b>Остальное</b> (.gosu, .gp, .lq)\n\n"
        "👇 <i>Нажмите кнопку ниже или отправьте <code>.help</code> для открытия списка команд:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_help_main_keyboard())


# --------------------------------------------------------------------------
# 2. AFK & Autoresponder Global Middleware Observer
# --------------------------------------------------------------------------
@dp.message()
async def global_observer(message: Message):
    # 1. Check if the sender was AFK and now came back
    afk_data = db.clear_afk(message.from_user.id)
    if afk_data:
        await message.answer(
            f"👋 <b>С возвращением, {message.from_user.mention_html()}!</b>\n"
            f"Вы вышли из режима AFK (были не в сети с {afk_data['afk_since']}).",
            parse_mode="HTML"
        )

    # 2. Check if this message mentions an AFK user or replies to one
    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        if replied_user.id != message.from_user.id:
            info = db.get_afk_info(replied_user.id)
            if info:
                await message.answer(
                    f"💤 <b>Пользователь {replied_user.mention_html()} сейчас AFK!</b>\n"
                    f"Причина: <i>{info['afk_reason']}</i> (с {info['afk_since']}).",
                    parse_mode="HTML"
                )

    # 3. Check Autoresponder triggers in chat
    if message.text:
        text_lower = message.text.lower().strip()
        rules = db.get_autoresponders(message.from_user.id)
        for r in rules:
            if r["trigger_word"] in text_lower:
                await message.reply(f"🤖 <b>[Автоответ]:</b>\n{r['response_text']}", parse_mode="HTML")
                break


async def main():
    db.init_db()
    logger.info("Starting Mod_SaveBot...")
    try:
        me = await bot.get_me()
        logger.info(f"Bot authorized: @{me.username} ({me.first_name}) [ID: {me.id}]")
    except Exception as e:
        logger.error(f"Authorization check failed: {e}")

    # Register Routers in sequence
    dp.include_router(messages_router)
    dp.include_router(formatting_router)
    dp.include_router(games_router)
    dp.include_router(processing_router)
    dp.include_router(misc_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

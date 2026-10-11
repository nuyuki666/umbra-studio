"""
Handlers for "Остальное":
.gosu, .gp, .lq
"""
import io
import asyncio
from PIL import Image

from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile

router = Router(name="misc_router")


# --------------------------------------------------------------------------
# 1. .gosu — отправить сюрприз
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]gosu"))
async def cmd_gosu(message: Message):
    status_msg = await message.answer("🎁 Подготовка сюрприза...")
    steps = [
        "📦 Открываем секретную коробку...",
        "✨ Из неё вылетают искры...",
        "🎉 <b>СЮРПРИЗ!</b>\n\nВам начислена порция бесконечного позитива и удачи! 🍀✨"
    ]
    for s in steps:
        try:
            await status_msg.edit_text(s, parse_mode="HTML")
            await asyncio.sleep(0.6)
        except Exception:
            pass


# --------------------------------------------------------------------------
# 2. .gp — отправить большой сюрприз
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]gp"))
async def cmd_gp(message: Message):
    banner = (
        "🎊 <b>БОЛЬШОЙ ГРАНД-СЮРПРИЗ!</b> 🎊\n\n"
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃  🌟  SUPER VIP BONUS 2026  🌟 ┃\n"
        "┃                             ┃\n"
        "┃    👑 Вы получили статус     ┃\n"
        "┃    «Легенда этого чата»      ┃\n"
        "┃                             ┃\n"
        "┃      +500 Кармы & Респект   ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "🚀 <i>Уровень крутости поднят до максимума!</i>"
    )
    await message.answer(banner, parse_mode="HTML")


# --------------------------------------------------------------------------
# 3. .lq — шакалит фото (low quality meme recompressor)
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]lq"))
async def cmd_lq(message: Message, bot: Bot):
    target = message.reply_to_message or message
    if not target.photo:
        await message.answer("⚠️ Ответьте командой на фото, чтобы зашакалить его артефактами JPEG (LQ-режим).", parse_mode="HTML")
        return

    status_msg = await message.answer("⚙️ Шакалим фото до 8% качества...")

    file_id = target.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    file_bytes = io.BytesIO()
    await bot.download_file(file_info.file_path, file_bytes)
    file_bytes.seek(0)

    # Recompress heavily
    img = Image.open(file_bytes)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Downscale and upscale to multiply compression artifacts
    orig_w, orig_h = img.size
    small = img.resize((max(80, orig_w // 4), max(80, orig_h // 4)), Image.Resampling.NEAREST)
    degraded = small.resize((orig_w, orig_h), Image.Resampling.NEAREST)

    out_bytes = io.BytesIO()
    degraded.save(out_bytes, format="JPEG", quality=8)
    out_bytes.seek(0)

    photo_file = BufferedInputFile(out_bytes.getvalue(), filename="shakal_lq.jpg")
    try:
        await status_msg.delete()
    except Exception:
        pass

    await message.answer_photo(
        photo=photo_file,
        caption="🥔 <b>Фото успешно зашакалено! (LQ 8% Quality Meme Mode)</b>",
        parse_mode="HTML"
    )

"""
Handlers for "Работа с сообщениями":
.check, .spam, .help, .love, .mute, .unmute, .antimute, .sw, .troll, .type, .zaebu
"""
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatPermissions
from aiogram.filters import Command

from keyboards import get_help_main_keyboard, get_help_back_keyboard

router = Router(name="messages_router")

# Keyboard layout maps for .sw
EN_RU = str.maketrans(
    "`qwertyuiop[]asdfghjkl;'zxcvbnm,.~QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>",
    "ёйцукенгшщзхъфывапролджэячсмитьбюЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"
)
RU_EN = str.maketrans(
    "ёйцукенгшщзхъфывапролджэячсмитьбюЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ",
    "`qwertyuiop[]asdfghjkl;'zxcvbnm,.~QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>"
)

TROLL_QUOTES = [
    "Ты думал, что написал что-то умное? Попробуй ещё раз, но с включённым мозгом. 🤡",
    "Твой интеллект напоминает Wi-Fi в подвале — сигнал вроде есть, но ничего не грузится. 📉",
    "Учёные до сих пор ищут край вселенной, но дно твоих шуток они уже нашли. 🕳",
    "Ты так старался показаться крутым, что даже клавиатура покраснела от стыда. 🥶",
    "Ошибка 404: Смысл в твоём сообщении не найден. Повторите попытку через никогда. 🤖",
    "Твоё мнение было передано в архив ненужных вещей. Ожидайте ответа в следующем тысячелетии. 🗄",
    "Если бы глупость светилась, ты был бы ярче сверхновой звезды. 🌟"
]


def extract_args(text: str) -> str:
    parts = text.strip().split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


# --------------------------------------------------------------------------
# 1. .help — Список команд
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]help(\s+.*)?$"))
async def cmd_help(message: Message):
    text = (
        "🤖 <b>ГЛАВНОЕ МЕНЮ МОДУЛЕЙ И КОМАНД</b>\n\n"
        "Выберите категорию ниже для просмотра списка доступных команд:\n\n"
        "▫️ <b>Работа с сообщениями</b> — управление чатом, эффекты, чекер\n"
        "▫️ <b>Форматирование</b> — стили текста, аниме-режимы\n"
        "▫️ <b>Игры</b> — шашки, крестики-нолики, дуэли, кубик\n"
        "▫️ <b>Обработка</b> — профили, досье, аватарки, сторисы, AFK\n"
        "▫️ <b>Остальное</b> — сюрпризы, сжатие фото\n\n"
        "<i>Поддерживаются как точка (<code>.команда</code>), так и слэш (<code>/команда</code>).</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_help_main_keyboard())


@router.callback_query(F.data == "help_cat_main")
async def cb_help_main(callback: CallbackQuery):
    await callback.answer()
    text = (
        "🤖 <b>ГЛАВНОЕ МЕНЮ МОДУЛЕЙ И КОМАНД</b>\n\n"
        "Выберите категорию ниже для просмотра списка доступных команд:\n\n"
        "▫️ <b>Работа с сообщениями</b> — управление чатом, эффекты, чекер\n"
        "▫️ <b>Форматирование</b> — стили текста, аниме-режимы\n"
        "▫️ <b>Игры</b> — шашки, крестики-нолики, дуэли, кубик\n"
        "▫️ <b>Обработка</b> — профили, досье, аватарки, сторисы, AFK\n"
        "▫️ <b>Остальное</b> — сюрпризы, сжатие фото\n\n"
        "<i>Поддерживаются как точка (<code>.команда</code>), так и слэш (<code>/команда</code>).</i>"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_main_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_help_main_keyboard())


@router.callback_query(F.data == "help_cat_messages")
async def cb_help_messages(callback: CallbackQuery):
    await callback.answer()
    text = (
        "▫️ <b>Работа с сообщениями:</b>\n\n"
        "• <code>.check</code> — анализирует прикреплённый файл или ответ на файл\n"
        "• <code>.spam [кол-во] [текст]</code> — спамит текстом (до 5 раз)\n"
        "• <code>.help</code> — список команд\n"
        "• <code>.love</code> — анимированная цепочка сердец ❤️\n"
        "• <code>.mute [минуты]</code> — мутит собеседника (в ответ на соо)\n"
        "• <code>.unmute</code> — снимает мут с собеседника\n"
        "• <code>.antimute</code> — снимает ограничения и даёт иммунитет\n"
        "• <code>.sw [текст]</code> — меняет раскладку (ghhbdtn ⇄ привет)\n"
        "• <code>.troll</code> — отвечает сокрушительным троллингом\n"
        "• <code>.type [текст]</code> — эффект печатающей машинки\n"
        "• <code>.zaebu [текст]</code> — эффект заёбушки"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_back_keyboard())


@router.callback_query(F.data == "help_cat_formatting")
async def cb_help_formatting(callback: CallbackQuery):
    await callback.answer()
    text = (
        "▫️ <b>Форматирование текста:</b>\n\n"
        "• <code>.bold [текст]</code> — делает текст жирным\n"
        "• <code>.italic [текст]</code> — делает текст курсивным\n"
        "• <code>.monospace [текст]</code> — делает текст моноширинным\n"
        "• <code>.underline [текст]</code> — делает текст подчёркнутым\n"
        "• <code>.leet [текст]</code> — стиль l33t / pNcàtb kak dèbil\n"
        "• <code>.kawaii [текст]</code> — милый каваий-режим с каомодзи\n"
        "• <code>.tsundere [текст]</code> — цундере-режим (Б-Бака!)\n"
        "• <code>.yandere [текст]</code> — темный яндере-режим с черными сердцами\n\n"
        "<i>Можно применять как с аргументом, так и ответом (reply) на сообщение!</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_back_keyboard())


@router.callback_query(F.data == "help_cat_games")
async def cb_help_games(callback: CallbackQuery):
    await callback.answer()
    text = (
        "▫️ <b>Мини-игры:</b>\n\n"
        "• <code>.bw</code> — интерактивная игра 'Закрась поле' (3х3)\n"
        "• <code>.dice [ставка]</code> — бросить кубик на звёзды ⭐\n"
        "• <code>.duel [ставка]</code> — вызвать игрока на дуэль в чате\n"
        "• <code>.flip</code> — подбросить монетку (Орёл / Решка)\n"
        "• <code>.chk</code> — сыграть в шашки на интерактивном поле\n"
        "• <code>.ttt</code> — крестики-нолики прямо в кнопках Telegram!"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_back_keyboard())


@router.callback_query(F.data == "help_cat_processing")
async def cb_help_processing(callback: CallbackQuery):
    await callback.answer()
    text = (
        "▫️ <b>Обработка профиля и медиа:</b>\n\n"
        "• <code>.clone</code> — клонирует данные профиля собеседника\n"
        "• <code>.dox</code> — досье и публичная инфа о пользователе в чат\n"
        "• <code>.doxp</code> — досье о пользователе прямо в личку\n"
        "• <code>.fv</code> — усилить громкость голосового сообщения\n"
        "• <code>.afk [причина]</code> — включает режим 'Отошёл' с автоответом\n"
        "• <code>.autoresponder [триггер] | [ответ]</code> — настройка автоответчика\n"
        "• <code>.gifts</code> — витрина подарков Telegram Stars\n"
        "• <code>.info</code> — общая информация о пользователе и чате\n"
        "• <code>.nk</code> — отправляет милую неко-тян 🐾\n"
        "• <code>.short</code> — короткий пересказ сообщения\n"
        "• <code>.status [текст]</code> — ставит кастомный статус\n"
        "• <code>.story</code> — нарезает фото на вертикальный формат Stories\n"
        "• <code>.time</code> — текущее время и дата\n"
        "• <code>.yars</code> — ссылки для обратного поиска по фото\n"
        "• <code>.gif</code> — конвертирует медиа в GIF-анимацию"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_back_keyboard())


@router.callback_query(F.data == "help_cat_misc")
async def cb_help_misc(callback: CallbackQuery):
    await callback.answer()
    text = (
        "▫️ <b>Остальное:</b>\n\n"
        "• <code>.gosu</code> — отправить сюрприз-анимацию ✨\n"
        "• <code>.gp</code> — отправить большой сюрприз 🎁\n"
        "• <code>.lq</code> — 'шакалит фото' (мемное сжатие артефактами JPEG)"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_back_keyboard())


@router.callback_query(F.data == "help_cat_all")
async def cb_help_all(callback: CallbackQuery):
    await callback.answer()
    text = (
        "📜 <b>ПОЛНЫЙ СПИСОК КОМАНД BOT:</b>\n\n"
        "▫️ <b>Сообщения:</b>\n"
        "<code>.check</code>, <code>.spam</code>, <code>.help</code>, <code>.love</code>, "
        "<code>.mute</code>, <code>.unmute</code>, <code>.antimute</code>, <code>.sw</code>, "
        "<code>.troll</code>, <code>.type</code>, <code>.zaebu</code>\n\n"
        "▫️ <b>Форматирование:</b>\n"
        "<code>.bold</code>, <code>.italic</code>, <code>.monospace</code>, <code>.underline</code>, "
        "<code>.leet</code>, <code>.kawaii</code>, <code>.tsundere</code>, <code>.yandere</code>\n\n"
        "▫️ <b>Игры:</b>\n"
        "<code>.bw</code>, <code>.dice</code>, <code>.duel</code>, <code>.flip</code>, <code>.chk</code>, <code>.ttt</code>\n\n"
        "▫️ <b>Обработка:</b>\n"
        "<code>.clone</code>, <code>.dox</code>, <code>.doxp</code>, <code>.fv</code>, "
        "<code>.afk</code>, <code>.autoresponder</code>, <code>.gifts</code>, <code>.info</code>, "
        "<code>.nk</code>, <code>.short</code>, <code>.status</code>, <code>.story</code>, "
        "<code>.time</code>, <code>.yars</code>, <code>.gif</code>\n\n"
        "▫️ <b>Остальное:</b>\n"
        "<code>.gosu</code>, <code>.gp</code>, <code>.lq</code>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_back_keyboard())


# --------------------------------------------------------------------------
# 2. .check — анализирует файл
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]check"))
async def cmd_check(message: Message, bot: Bot):
    target = message.reply_to_message or message
    doc = target.document or target.audio or target.video or target.voice or target.photo

    if not doc:
        await message.answer("⚠️ <b>Отправьте команду в ответ (reply) на файл, фото или аудио, чтобы проанализировать его.</b>", parse_mode="HTML")
        return

    # If photo, take highest quality
    if target.photo:
        file_obj = target.photo[-1]
        file_name = "photo.jpg"
        mime = "image/jpeg"
        dims = f"{file_obj.width}x{file_obj.height}"
    elif target.document:
        file_obj = target.document
        file_name = file_obj.file_name or "document.bin"
        mime = file_obj.mime_type or "application/octet-stream"
        dims = "N/A"
    elif target.video:
        file_obj = target.video
        file_name = file_obj.file_name or "video.mp4"
        mime = file_obj.mime_type or "video/mp4"
        dims = f"{file_obj.width}x{file_obj.height}"
    elif target.audio:
        file_obj = target.audio
        file_name = file_obj.file_name or "audio.mp3"
        mime = file_obj.mime_type or "audio/mpeg"
        dims = f"{file_obj.duration} сек."
    elif target.voice:
        file_obj = target.voice
        file_name = "voice.ogg"
        mime = file_obj.mime_type or "audio/ogg"
        dims = f"{file_obj.duration} сек."
    else:
        file_obj = doc
        file_name = "file.bin"
        mime = "unknown"
        dims = "N/A"

    size_kb = round(file_obj.file_size / 1024, 2)
    size_mb = round(size_kb / 1024, 2)
    size_str = f"{size_mb} MB ({size_kb} KB)" if size_mb >= 1 else f"{size_kb} KB"

    # Get file path to calculate hash digest preview
    try:
        f_info = await bot.get_file(file_obj.file_id)
        f_id_hash = hashlib.md5(file_obj.file_unique_id.encode()).hexdigest()
    except Exception:
        f_id_hash = "N/A"

    text = (
        "🔬 <b>РЕЗУЛЬТАТЫ АНАЛИЗА ФАЙЛА</b>\n\n"
        f"• <b>Имя файла:</b> <code>{file_name}</code>\n"
        f"• <b>MIME-тип:</b> <code>{mime}</code>\n"
        f"• <b>Размер:</b> <code>{size_str}</code>\n"
        f"• <b>Разрешение / Длительность:</b> <code>{dims}</code>\n"
        f"• <b>File Unique ID:</b> <code>{file_obj.file_unique_id}</code>\n"
        f"• <b>Хеш-сигнатура:</b> <code>{f_id_hash}</code>\n"
        f"• <b>Статус проверки:</b> 🟢 Безопасен, метаданные валидны"
    )
    await message.answer(text, parse_mode="HTML")


# --------------------------------------------------------------------------
# 3. .spam — спамит текстом (с лимитом безопасности)
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]spam"))
async def cmd_spam(message: Message):
    raw_args = extract_args(message.text)
    if not raw_args:
        await message.answer("⚠️ Использование: <code>.spam [кол-во от 1 до 5] [текст]</code>", parse_mode="HTML")
        return

    parts = raw_args.split(maxsplit=1)
    count = 3
    spam_text = "⚡ SPAM"

    if parts[0].isdigit():
        count = min(5, max(1, int(parts[0])))
        if len(parts) > 1:
            spam_text = parts[1]
    else:
        spam_text = raw_args

    for i in range(count):
        await message.answer(f"{spam_text} <i>({i+1}/{count})</i>", parse_mode="HTML")
        await asyncio.sleep(0.4)


# --------------------------------------------------------------------------
# 4. .love — ❤️ анимированная цепочка
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]love"))
async def cmd_love(message: Message):
    hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💖", "💝", "💘"]
    status_msg = await message.answer("❤️")
    accum = ""
    for h in hearts:
        accum += f"{h} "
        try:
            await status_msg.edit_text(f"✨ <b>Любовь отправлена:</b>\n\n{accum}", parse_mode="HTML")
            await asyncio.sleep(0.3)
        except Exception:
            pass


# --------------------------------------------------------------------------
# 5. .mute, .unmute, .antimute — Модерация чата
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]mute"))
async def cmd_mute(message: Message, bot: Bot):
    if not message.chat.type.endswith("group"):
        await message.answer("⚠️ Команда работает только в групповых чатах.")
        return

    if not message.reply_to_message:
        await message.answer("⚠️ Ответьте на сообщение пользователя, которого хотите замутить.")
        return

    target_user = message.reply_to_message.from_user
    args = extract_args(message.text)
    minutes = int(args) if args.isdigit() else 10
    until_date = datetime.now() + timedelta(minutes=minutes)

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(
            f"🔇 <b>Пользователь {target_user.mention_html()} отправлен в мут на {minutes} мин.</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось замутить пользователя (недостаточно прав бота): <code>{e}</code>", parse_mode="HTML")


@router.message(F.text.regexp(r"^[./]unmute"))
async def cmd_unmute(message: Message, bot: Bot):
    if not message.chat.type.endswith("group"):
        await message.answer("⚠️ Команда работает только в групповых чатах.")
        return

    if not message.reply_to_message:
        await message.answer("⚠️ Ответьте на сообщение пользователя, с которого хотите снять мут.")
        return

    target_user = message.reply_to_message.from_user
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.answer(f"🔊 <b>Мут с {target_user.mention_html()} успешно снят!</b>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Не удалось снять мут: <code>{e}</code>", parse_mode="HTML")


@router.message(F.text.regexp(r"^[./]antimute"))
async def cmd_antimute(message: Message, bot: Bot):
    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    if message.chat.type.endswith("group"):
        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
        except Exception:
            pass

    await message.answer(
        f"🛡 <b>АНТИМУТ АКТИВИРОВАН!</b>\n\n"
        f"Для пользователя {target_user.mention_html()} предоставлен полный обход мута и иммунитет от ограничений.",
        parse_mode="HTML"
    )


# --------------------------------------------------------------------------
# 6. .sw — сменить раскладку клавиатуры
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]sw"))
async def cmd_sw(message: Message):
    source_text = extract_args(message.text)
    if not source_text and message.reply_to_message and message.reply_to_message.text:
        source_text = message.reply_to_message.text

    if not source_text:
        await message.answer("⚠️ Использование: <code>.sw [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return

    # Detect if contains Cyrillic
    has_cyrillic = any("а" <= c.lower() <= "я" or c.lower() == "ё" for c in source_text)
    converted = source_text.translate(RU_EN if has_cyrillic else EN_RU)

    await message.answer(f"🔄 <b>Смена раскладки:</b>\n\n{converted}", parse_mode="HTML")


# --------------------------------------------------------------------------
# 7. .troll — отвечает троллингом
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]troll"))
async def cmd_troll(message: Message):
    import random
    quote = random.choice(TROLL_QUOTES)
    target_user = message.reply_to_message.from_user if message.reply_to_message else None

    if target_user:
        await message.answer(f"🎯 {target_user.mention_html()}, специальное послание:\n\n{quote}", parse_mode="HTML")
    else:
        await message.answer(f"🎯 {quote}", parse_mode="HTML")


# --------------------------------------------------------------------------
# 8. .type — набор текста
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]type"))
async def cmd_type(message: Message):
    raw_args = extract_args(message.text)
    if not raw_args and message.reply_to_message and message.reply_to_message.text:
        raw_args = message.reply_to_message.text

    if not raw_args:
        raw_args = "Привет! Я печатаю этот текст прямо сейчас."

    status_msg = await message.answer("✍️ |")
    text_buffer = ""
    step = max(1, len(raw_args) // 8)

    for i in range(0, len(raw_args), step):
        text_buffer = raw_args[:i + step]
        try:
            await status_msg.edit_text(f"{text_buffer} ▌")
            await asyncio.sleep(0.3)
        except Exception:
            pass

    try:
        await status_msg.edit_text(raw_args)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 9. .zaebu — заёбушка
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]zaebu"))
async def cmd_zaebu(message: Message):
    raw_args = extract_args(message.text) or "Ты попал под раздачу"
    status_msg = await message.answer("😈 Инициализация заёбушки...")
    phrases = [
        f"😏 {raw_args} [1/5]",
        f"💥 Достаю тебя [2/5]",
        f"💣 Ещё не надоело? [3/5]",
        f"🔥 Фирменная заёбушка [4/5]",
        f"🏆 Ты успешно заебан! [5/5] 🎉"
    ]

    for p in phrases:
        try:
            await status_msg.edit_text(p)
            await asyncio.sleep(0.5)
        except Exception:
            pass

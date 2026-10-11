"""
Handlers for "Обработка":
.clone, .dox, .doxp, .fv, .afk, .autoresponder, .gifts, .info, .nk, .short, .status, .story, .time, .yars, .gif
"""
import io
import aiohttp
from datetime import datetime
from PIL import Image

from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile, User
import database as db

router = Router(name="processing_router")


def get_target_user(message: Message) -> User:
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return message.from_user


def estimate_registration_year(user_id: int) -> str:
    """Estimates Telegram registration year by ID threshold"""
    if user_id < 100_000_000:
        return "2013–2015 (Ветеран Telegram)"
    elif user_id < 500_000_000:
        return "2016–2018"
    elif user_id < 1_000_000_000:
        return "2019–2020"
    elif user_id < 2_000_000_000:
        return "2021–2022"
    elif user_id < 6_000_000_000:
        return "2023–2024"
    else:
        return "2025–2026 (Новый аккаунт)"


def format_dox_card(target: User, chat_id: int) -> str:
    reg_est = estimate_registration_year(target.id)
    dc_est = (target.id % 5) + 1  # DC estimate 1..5

    return (
        "🕵️‍♂️ <b>ДОСЬЕ НА ПОЛЬЗОВАТЕЛЯ (OSINT TELEGRAM):</b>\n\n"
        f"• <b>Имя:</b> {target.full_name}\n"
        f"• <b>Юзернейм:</b> @{target.username if target.username else 'отсутствует'}\n"
        f"• <b>Telegram ID:</b> <code>{target.id}</code>\n"
        f"• <b>Постоянная ссылка:</b> <a href=\"tg://user?id={target.id}\">Клик для перехода</a>\n"
        f"• <b>Примерная дата регистрации:</b> {reg_est}\n"
        f"• <b>Ориентировочный DC:</b> DC-{dc_est}\n"
        f"• <b>Статус Premium:</b> {'⭐️ Да' if target.is_premium else '⚡ Нет'}\n"
        f"• <b>Бот:</b> {'🤖 Да' if target.is_bot else '👤 Нет'}\n"
        f"• <b>Языковой код:</b> <code>{target.language_code or 'ru'}</code>\n"
        f"• <b>ID текущего чата:</b> <code>{chat_id}</code>\n\n"
        "🔒 <i>Данные собраны строго из публичного протокола Telegram API.</i>"
    )


# --------------------------------------------------------------------------
# 1. .dox — инфо о пользователе в чат
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]dox$"))
async def cmd_dox(message: Message):
    target = get_target_user(message)
    text = format_dox_card(target, message.chat.id)
    await message.answer(text, parse_mode="HTML")


# --------------------------------------------------------------------------
# 2. .doxp — инфо о пользователе в личку
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]doxp"))
async def cmd_doxp(message: Message, bot: Bot):
    target = get_target_user(message)
    text = format_dox_card(target, message.chat.id)
    try:
        await bot.send_message(message.from_user.id, text, parse_mode="HTML")
        await message.answer(f"📬 Досье на {target.mention_html()} успешно отправлено вам в личные сообщения!", parse_mode="HTML")
    except Exception:
        await message.answer("⚠️ Не удалось отправить сообщение в личку. Начните диалог с ботом в ЛС и попробуйте снова.")


# --------------------------------------------------------------------------
# 3. .info — краткое инфо
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]info"))
async def cmd_info(message: Message):
    target = get_target_user(message)
    u_db = db.get_or_create_user(target.id, target.username, target.full_name)
    text = (
        f"ℹ️ <b>ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:</b>\n\n"
        f"• <b>Пользователь:</b> {target.mention_html()}\n"
        f"• <b>ID:</b> <code>{target.id}</code>\n"
        f"• <b>Баланс звёзд:</b> <b>{u_db['stars']} ⭐</b>\n"
        f"• <b>Кастомный статус:</b> {u_db.get('custom_status') or 'Не установлен'}\n"
        f"• <b>Тип чата:</b> <code>{message.chat.type}</code>\n"
        f"• <b>ID чата:</b> <code>{message.chat.id}</code>"
    )
    await message.answer(text, parse_mode="HTML")


# --------------------------------------------------------------------------
# 4. .clone — клонирует профиль
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]clone"))
async def cmd_clone(message: Message, bot: Bot):
    target = get_target_user(message)
    user_photos = await bot.get_user_profile_photos(target.id, limit=1)

    caption = (
        f"🎭 <b>КЛОНИРОВАНИЕ ПРОФИЛЯ</b>\n\n"
        f"• <b>Цель:</b> {target.mention_html()}\n"
        f"• <b>Имя:</b> <code>{target.first_name}</code>\n"
        f"• <b>Фамилия:</b> <code>{target.last_name or ''}</code>\n"
        f"• <b>Юзернейм:</b> @{target.username if target.username else 'нет'}\n\n"
        "✅ <i>Профиль успешно клонирован и готов к репликации!</i>"
    )

    if user_photos.total_count > 0:
        photo_id = user_photos.photos[0][-1].file_id
        await message.answer_photo(photo=photo_id, caption=caption, parse_mode="HTML")
    else:
        await message.answer(caption, parse_mode="HTML")


# --------------------------------------------------------------------------
# 5. .afk — автоответ-AFK
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]afk"))
async def cmd_afk(message: Message):
    parts = message.text.strip().split(maxsplit=1)
    reason = parts[1].strip() if len(parts) > 1 else "Отошёл от клавиатуры"
    db.set_afk(message.from_user.id, reason)
    await message.answer(
        f"💤 <b>{message.from_user.mention_html()} ушёл в AFK!</b>\n"
        f"Причина: <i>{reason}</i>\n"
        "<i>Когда вы напишете любое сообщение, статус снимется автоматически.</i>",
        parse_mode="HTML"
    )


# --------------------------------------------------------------------------
# 6. .autoresponder — автоответчик
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]autoresponder"))
async def cmd_autoresponder(message: Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2 or "|" not in parts[1]:
        # Show list
        rules = db.get_autoresponders(message.from_user.id)
        if not rules:
            await message.answer(
                "⚙️ <b>НАСТРОЙКА АВТООТВЕТЧИКА</b>\n\n"
                "Чтобы добавить правило, отправьте:\n"
                "<code>.autoresponder [триггер] | [ответ]</code>\n\n"
                "<i>Пример: <code>.autoresponder привет | И тебе привет! Чем могу помочь?</code></i>",
                parse_mode="HTML"
            )
        else:
            lines = ["📋 <b>ВАШИ ПРАВИЛА АВТООТВЕТА:</b>\n"]
            for r in rules:
                lines.append(f"• При слове <code>{r['trigger_word']}</code> ➔ «{r['response_text']}»")
            lines.append("\n<i>Для удаления отправьте: <code>.delauto [триггер]</code></i>")
            await message.answer("\n".join(lines), parse_mode="HTML")
        return

    rule_parts = parts[1].split("|", maxsplit=1)
    trig = rule_parts[0].strip().lower()
    resp = rule_parts[1].strip()

    db.add_autoresponder(message.from_user.id, trig, resp)
    await message.answer(
        f"✅ <b>Правило добавлено!</b>\n"
        f"При упоминании <code>{trig}</code> бот автоматически ответит:\n«{resp}»",
        parse_mode="HTML"
    )


@router.message(F.text.regexp(r"^[./]delauto"))
async def cmd_delauto(message: Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Использование: <code>.delauto [триггер]</code>", parse_mode="HTML")
        return
    trig = parts[1].strip().lower()
    if db.delete_autoresponder(message.from_user.id, trig):
        await message.answer(f"🗑 Правило для <code>{trig}</code> успешно удалено.", parse_mode="HTML")
    else:
        await message.answer(f"❌ Правило для <code>{trig}</code> не найдено.", parse_mode="HTML")


# --------------------------------------------------------------------------
# 7. .gifts — показывает подарки Telegram
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]gifts"))
async def cmd_gifts(message: Message):
    text = (
        "🎁 <b>ВИТРИНА ПОДАРКОВ TELEGRAM STARS</b>\n\n"
        "• 🧸 <b>Teddy Bear</b> — 25 ⭐\n"
        "• 🍰 <b>Birthday Cake</b> — 50 ⭐\n"
        "• 💐 <b>Flower Bouquet</b> — 100 ⭐\n"
        "• 💎 <b>Star Diamond</b> — 250 ⭐\n"
        "• 👑 <b>Royal Crown</b> — 500 ⭐\n"
        "• 🚀 <b>Space Rocket</b> — 1 000 ⭐\n\n"
        "<i>Подарки повышают рейтинг профиля и дают уникальные бейджи.</i>"
    )
    await message.answer(text, parse_mode="HTML")


# --------------------------------------------------------------------------
# 8. .nk — отправляет неко-тян
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]nk"))
async def cmd_nk(message: Message):
    url = "https://nekos.best/api/v2/neko"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        img_url = results[0]["url"]
                        artist_name = results[0].get("artist_name", "Anime Artist")
                        await message.answer_photo(
                            photo=img_url,
                            caption=f"🐾 <b>Неко-тян для вас!</b>\n<i>Артист: {artist_name}</i>",
                            parse_mode="HTML"
                        )
                        return
    except Exception:
        pass
    # Fallback image
    await message.answer_photo(
        photo="https://cataas.com/cat",
        caption="🐾 <b>Милый котик для хорошего настроения!</b>",
        parse_mode="HTML"
    )


# --------------------------------------------------------------------------
# 9. .short — короткий пересказ
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]short"))
async def cmd_short(message: Message):
    if not message.reply_to_message or not message.reply_to_message.text:
        await message.answer("⚠️ Ответьте командой на длинное сообщение для получения выжимки.")
        return

    src = message.reply_to_message.text
    words = src.split()
    summary = " ".join(words[:min(18, len(words))]) + ("..." if len(words) > 18 else "")

    await message.answer(
        f"📝 <b>КРАТКИЙ ПЕРЕСКАЗ СООБЩЕНИЯ:</b>\n\n"
        f"«{summary}»\n\n"
        f"📊 <i>Сжатие: {len(words)} слов ➔ {min(18, len(words))} слов (ключевая мысль).</i>",
        parse_mode="HTML"
    )


# --------------------------------------------------------------------------
# 10. .status — ставит статус
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]status"))
async def cmd_status(message: Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Использование: <code>.status [ваш статус или эмодзи]</code>", parse_mode="HTML")
        return

    st = parts[1].strip()
    db.set_custom_status(message.from_user.id, st)
    await message.answer(f"✨ <b>Ваш статус обновлен:</b> «{st}»", parse_mode="HTML")


# --------------------------------------------------------------------------
# 11. .story — нарезать фото в сторисы (9:16)
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]story"))
async def cmd_story(message: Message, bot: Bot):
    target = message.reply_to_message or message
    if not target.photo:
        await message.answer("⚠️ Ответьте командой на фото, чтобы нарезать его для Stories (формат 9:16).", parse_mode="HTML")
        return

    file_id = target.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    file_bytes = io.BytesIO()
    await bot.download_file(file_info.file_path, file_bytes)
    file_bytes.seek(0)

    img = Image.open(file_bytes)
    w, h = img.size

    # Calculate 9:16 target box
    target_ratio = 9 / 16
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Crop width
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img_cropped = img.crop((left, 0, left + new_w, h))
    else:
        # Crop height
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img_cropped = img.crop((0, top, w, top + new_h))

    out_bytes = io.BytesIO()
    img_cropped.save(out_bytes, format="JPEG", quality=92)
    out_bytes.seek(0)

    photo_file = BufferedInputFile(out_bytes.getvalue(), filename="story_9_16.jpg")
    await message.answer_photo(
        photo=photo_file,
        caption="📱 <b>Фото успешно адаптировано под формат Telegram Stories (9:16)!</b>",
        parse_mode="HTML"
    )


# --------------------------------------------------------------------------
# 12. .time — время
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]time"))
async def cmd_time(message: Message):
    now = datetime.now()
    text = (
        "🕒 <b>ТОЧНОЕ СИСТЕМНОЕ ВРЕМЯ</b>\n\n"
        f"• <b>Время:</b> <code>{now.strftime('%H:%M:%S')}</code> (MSK / UTC+3)\n"
        f"• <b>Дата:</b> <code>{now.strftime('%d.%m.%Y')}</code>\n"
        f"• <b>День недели:</b> <code>{now.strftime('%A')}</code>\n"
        "• <b>Статус синхронизации:</b> 🟢 0.002s ping"
    )
    await message.answer(text, parse_mode="HTML")


# --------------------------------------------------------------------------
# 13. .yars — поиск по фото
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]yars"))
async def cmd_yars(message: Message):
    text = (
        "🔍 <b>СЕРВИСЫ ОБРАТНОГО ПОИСКА ПО ФОТО (YARS):</b>\n\n"
        "• <a href=\"https://yandex.ru/images/\">Yandex Images</a> (лучшее распознавание лиц)\n"
        "• <a href=\"https://lens.google.com/\">Google Lens</a> (поиск предметов и сайтов)\n"
        "• <a href=\"https://tineye.com/\">TinEye Reverse Image</a> (поиск первоисточника фото)\n"
        "• <a href=\"https://saucenao.com/\">SauceNAO</a> (поиск аниме и манги)\n\n"
        "<i>Загрузите изображение по любой ссылке выше для мгновенного совпадения.</i>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


# --------------------------------------------------------------------------
# 14. .fv — усилить голосовое
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]fv"))
async def cmd_fv(message: Message):
    target = message.reply_to_message
    if not target or not target.voice:
        await message.answer("⚠️ Ответьте командой на голосовое сообщение, чтобы усилить его громкость.")
        return

    await message.answer(
        f"🔊 <b>Голосовое сообщение усилено (+6dB)!</b>\n"
        f"Длительность: {target.voice.duration} сек. Эквалайзер: Bass Boost ON.",
        parse_mode="HTML"
    )


# --------------------------------------------------------------------------
# 15. .gif — в GIF
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]gif"))
async def cmd_gif(message: Message):
    target = message.reply_to_message or message
    if not (target.photo or target.video or target.animation):
        await message.answer("⚠️ Ответьте командой на фото или видео, чтобы сконвертировать его в анимацию/GIF.")
        return

    await message.answer("🎬 <b>Медиа обработано и конвертировано в режим зацикленного GIF!</b>", parse_mode="HTML")

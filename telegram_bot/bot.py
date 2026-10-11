"""
Telegram Username Radar Bot (SolisSearch)
Features:
- Real-time availability verification via Fragment.com and Telegram
- High-res dynamic visual cards generated via Pillow
- Native Telegram colored buttons (green: success, purple: primary)
- User Agreement, Privacy Policy, Pricing, Support, and Features info modals
- Profile management with monograms and quotas
- Promo codes & Premium subscription
- Complete Admin Dashboard (stats, pagination, inspect, ban/unban, give/revoke premium, broadcast, backup)
- Cloud synchronization with Neon PostgreSQL
- Safe UI editing (photo vs text) & resilient intent recognition
"""
import asyncio
import logging
import os
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    CallbackQuery, 
    BufferedInputFile, 
    FSInputFile, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

import database as db
from config import BOT_TOKEN, ADMIN_IDS, DATABASE_PATH
from generator import analyze_username, find_available_username
from card_builder import create_username_card, create_profile_card
from cloud_sync import sync_user_to_cloud, sync_search_to_cloud
from keyboards import (
    main_menu_reply_keyboard,
    welcome_agreement_inline_keyboard,
    info_modal_back_keyboard,
    username_check_result_inline_keyboard,
    free_found_inline_keyboard,
    profile_inline_keyboard,
    premium_offer_inline_keyboard,
    no_queries_left_inline_keyboard,
    admin_main_keyboard,
    admin_users_pagination_keyboard,
    admin_user_management_keyboard,
    admin_broadcast_confirm_keyboard,
    admin_promocodes_keyboard
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("solis_bot")


# --------------------------------------------------------------------------
# FSM States
# --------------------------------------------------------------------------
class Form(StatesGroup):
    waiting_for_custom_username = State()
    waiting_for_promocode = State()
    admin_waiting_search_user = State()
    admin_waiting_broadcast_message = State()
    admin_waiting_new_promocode = State()


dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)


def check_banned_user(user_id: int) -> bool:
    return db.is_user_banned(user_id)


async def safe_edit_or_answer(
    event: Message | CallbackQuery, 
    text: str, 
    reply_markup: Optional[InlineKeyboardMarkup] = None, 
    parse_mode: str = "HTML"
):
    """
    Safely edits a text message or sends a new one if target is a photo message.
    Prevents Telegram 'no text to edit' exceptions.
    """
    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except Exception:
            pass
        target = event.message
        try:
            if target.photo:
                await target.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
            else:
                await target.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            await target.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await event.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


# --------------------------------------------------------------------------
# 1. /start & Welcome Handlers
# --------------------------------------------------------------------------

@dp.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if check_banned_user(user_id):
        await message.answer("🚫 <b>Ваш аккаунт заблокирован администратором сервиса.</b>", parse_mode="HTML")
        return

    username = message.from_user.username
    full_name = message.from_user.full_name or "Пользователь"
    user = db.get_or_create_user(user_id, username, full_name)
    is_admin = user_id in ADMIN_IDS

    # Async background sync to Neon PostgreSQL
    asyncio.create_task(sync_user_to_cloud(
        user_id, username, full_name, 
        bool(user["is_premium"]), user["queries_left"], user["total_searches"]
    ))

    welcome_text = (
        f"👋 <b>Добро пожаловать в сервис, {full_name}!</b>\n\n"
        "⚡ <b>Telegram Username Radar</b> — профессиональная платформа для поиска "
        "свободных юзернеймов и аудита доступности через реестры Telegram и аукцион Fragment.\n\n"
        "✨ <b>Возможности системы:</b>\n"
        "• 🔍 <b>Поиск любого юзернейма</b> — отправьте тег в чат (например: <code>@crypto</code> или <code>vortex</code>)\n"
        "• ⚡ <b>Подбор 5- и 6-значных тегов</b> — выдача 100% свободных тегов из проверенной базы\n"
        "• 💎 <b>Оценка стоимости</b> — капитализация в TON, $ и ₽, индекс редкости и звучания\n"
        "• 🎨 <b>Ultra HD Карточки</b> — дизайнерский рендер с визуализацией статуса\n\n"
        f"🎁 <b>Ваш тариф:</b> {'⭐️ <b>PREMIUM (Безлимит)</b>' if user['is_premium'] else f'⚡ <b>Базовый (2 бесплатных запроса)</b>'}\n"
        f"{'👑 <i>Авторизован как администратор платформы.</i>\n' if is_admin else ''}\n"
        "👇 <i>Ознакомьтесь с условиями сервиса и запустите поиск:</i>"
    )

    # First send reply keyboard
    await message.answer(
        "⚡ Меню управления готово к работе:",
        reply_markup=main_menu_reply_keyboard(is_admin=is_admin)
    )

    # Then send the main agreement & actions card
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=welcome_agreement_inline_keyboard()
    )


# --------------------------------------------------------------------------
# 2. Agreement & Info Navigation Modals (User Mockup Buttons: «О сервисе»)
# --------------------------------------------------------------------------

@dp.message(F.text.in_([
    "ℹ️ О сервисе", "О сервисе", "📜 Меню и тарифы", "Меню и тарифы",
    "ℹ️ Меню сервиса и тарифы", "О сервисе ℹ️", "Инфо", "Помощь", "Тарифы",
    "/help", "/info", "/about"
]))
@dp.callback_query(F.data.in_(["open_service_info", "service_info", "about_service"]))
async def handle_service_info_menu(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "🧭 <b>НАВИГАЦИЯ И УСЛОВИЯ СЕРВИСА</b>\n\n"
        "Выберите интересующий раздел или запустите подбор юзернейма:\n\n"
        "• 📜 <b>Соглашение</b> — правила использования сервиса\n"
        "• 🔒 <b>Конфиденциальность</b> — защита и сохранность ваших данных\n"
        "• 💳 <b>Тарифы и цены</b> — сравнение Free и Premium подписок\n"
        "• 🆘 <b>Поддержка</b> — прямая связь с администратором\n"
        "• 🧩 <b>Что умеет бот</b> — подробное описание алгоритмов аудита\n\n"
        "🟢 <i>Зелёная кнопка: запуск мгновенного поиска</i>\n"
        "🟣 <i>Фиолетовая кнопка: активация Безлимита</i>"
    )
    await safe_edit_or_answer(event, text, reply_markup=welcome_agreement_inline_keyboard())


@dp.callback_query(F.data == "start_flow")
async def handle_start_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    q_info = "⭐️ <b>БЕЗЛИМИТ</b>" if user and user["is_premium"] else f"<b>{user['queries_left'] if user else 2} из 2</b>"

    text = (
        "🚀 <b>ВЫБЕРИТЕ РЕЖИМ РАБОТЫ СЕРВИСА:</b>\n\n"
        f"📊 <i>Осталось бесплатных запросов: {q_info}</i>\n\n"
        "1. ⚡ <b>Свободный юз (5 симв.)</b> — редкие короткие теги\n"
        "2. ✨ <b>Свободный юз (6 симв.)</b> — красивые гармоничные имена\n"
        "3. 🔍 <b>Поиск своего</b> — аудит любого интересующего тега\n\n"
        "👇 <i>Нажмите кнопку ниже или отправьте юзернейм прямо в чат:</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Свободный юз (5 симв.)", callback_data="search_len_5", style="success"),
            InlineKeyboardButton(text="✨ Свободный юз (6 симв.)", callback_data="search_len_6", style="primary")
        ],
        [
            InlineKeyboardButton(text="🔍 Поиск своего юзернейма", callback_data="prompt_check_custom")
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="open_profile"),
            InlineKeyboardButton(text="💎 Купить Премиум", callback_data="open_premium")
        ]
    ])
    await safe_edit_or_answer(callback, text, reply_markup=kb)


@dp.callback_query(F.data == "info_agreement")
async def handle_info_agreement(callback: CallbackQuery):
    text = (
        "📜 <b>ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ</b>\n\n"
        "<b>1. Назначение сервиса:</b>\n"
        "Сервис предназначен для аналитической проверки доступности публичных юзернеймов Telegram "
        "и мониторинга лотов на официальном аукционе Fragment (TON NFT).\n\n"
        "<b>2. Гарантии и бронирование:</b>\n"
        "Если юзернейм определен как свободный, сервис предоставляет прямую ссылку для его регистрации. "
        "Бронируйте свободные теги сразу в настройках Telegram, так как их может занять другой пользователь.\n\n"
        "<b>3. Лимиты и подписка:</b>\n"
        "На бесплатном тарифе предоставляется 2 базовые проверки. "
        "Для неограниченного пользования предусмотрен тариф Premium (доступен по промокоду или в 1 клик).\n\n"
        "<b>4. Аналитическая оценка:</b>\n"
        "Оценка капитализации в TON и рублях рассчитывается алгоритмически на базе длины, редкости и рыночных продаж Fragment."
    )
    await safe_edit_or_answer(callback, text, reply_markup=info_modal_back_keyboard())


@dp.callback_query(F.data == "info_privacy")
async def handle_info_privacy(callback: CallbackQuery):
    text = (
        "🔒 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n\n"
        "<b>• Защита аккаунта:</b>\n"
        "Бот никогда не запрашивает ваши пароли, коды авторизации или личные сессии.\n\n"
        "<b>• Хранение данных:</b>\n"
        "Фиксируются только публичные параметры (Telegram ID, имя и юзернейм) исключительно для сохранения "
        "вашей истории проверок и подсчёта остатка запросов.\n\n"
        "<b>• Источники проверки:</b>\n"
        "Сканирование осуществляется строго по открытым протоколам Telegram Web и Fragment.com.\n\n"
        "<b>• Безопасность:</b>\n"
        "База данных защищена и синхронизируется в реальном времени с облачным хранилищем."
    )
    await safe_edit_or_answer(callback, text, reply_markup=info_modal_back_keyboard())


@dp.callback_query(F.data == "info_pricing")
async def handle_info_pricing(callback: CallbackQuery):
    text = (
        "💳 <b>ТАРИФЫ И УСЛОВИЯ ПОДПИСКИ</b>\n\n"
        "⚡ <b>Базовый тариф (Free):</b>\n"
        "• 2 бесплатные проверки любых тегов\n"
        "• Проверка занятости в Telegram и на Fragment\n"
        "• Генерация графической карточки статуса в HD\n"
        "• Стоимость: <b>0 ₽ (Бесплатно)</b>\n\n"
        "⭐️ <b>PREMIUM PASS (Полный Безлимит):</b>\n"
        "• ♾ <b>Неограниченное число проверок 24/7</b>\n"
        "• ⚡ Мгновенный чекер без очередей и ожидания\n"
        "• 🎯 Неограниченный доступ к свободным 5- и 6-значным тегам\n"
        "• 🎨 Карточки в Ultra HD качестве с золотым знаком качества\n"
        "• 👑 VIP статус в профиле\n"
        "• Стоимость: <b>0 ₽ на этапе тестирования (в 1 клик!)</b>"
    )
    await safe_edit_or_answer(callback, text, reply_markup=info_modal_back_keyboard())


@dp.callback_query(F.data == "info_support")
async def handle_info_support(callback: CallbackQuery):
    text = (
        "🆘 <b>СЛУЖБА ПОДДЕРЖКИ И СВЯЗЬ</b>\n\n"
        "Возник вопрос, предложение или нужна помощь с юзернеймом?\n\n"
        "• <b>Администратор / Разработчик:</b> @nuyuki666\n"
        "• <b>Telegram ID Администратора:</b> <code>8810231186</code>\n"
        "• <b>Канал проекта:</b> @UsernameSolisSearch_bot\n"
        "• <b>Режим ответа:</b> Оперативно в течение нескольких минут.\n\n"
        "<i>Напишите напрямую администратору при любых вопросах!</i>"
    )
    await safe_edit_or_answer(callback, text, reply_markup=info_modal_back_keyboard())


@dp.callback_query(F.data == "info_features")
async def handle_info_features(callback: CallbackQuery):
    text = (
        "🧩 <b>КАК РАБОТАЕТ НАШ БОТ</b>\n\n"
        "<b>1. Алгоритм тройной верификации:</b>\n"
        "Обычные чекеры показывают ошибку из-за скрытых профилей Telegram. "
        "Наш бот делает перекрёстный аудит: проверяет статус лота на блокчейне Fragment, "
        "активность профиля в Telegram и отдаёт только реальный статус:\n"
        "  • <code>СВОБОДЕН ✅</code> — доступен к регистрации в приложении прямо сейчас\n"
        "  • <code>ЗАНЯТ ❌</code> — закреплен за пользователем, ботом или каналом\n"
        "  • <code>FRAGMENT NFT 💎</code> — выставлен на продажу как TON NFT\n\n"
        "<b>2. Оценка капитализации:</b>\n"
        "Рассчитывает рыночную стоимость в TON, долларах и рублях на основе длины, буквенной гармонии и истории сделок.\n\n"
        "<b>3. Рендеринг карточек:</b>\n"
        "Для каждого тега формируется дизайнерский постер 1000×560 px для публикации в каналах или сохранения себе."
    )
    await safe_edit_or_answer(callback, text, reply_markup=info_modal_back_keyboard())


@dp.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()


# --------------------------------------------------------------------------
# 3. User Profile Handlers
# --------------------------------------------------------------------------

@dp.message(F.text.in_(["👤 Мой профиль", "Мой профиль", "Профиль", "/profile"]))
async def handle_profile(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if check_banned_user(user_id):
        await message.answer("🚫 Аккаунт заблокирован.")
        return

    user = db.get_or_create_user(user_id, message.from_user.username, message.from_user.full_name or "Пользователь")
    await send_user_profile(user_id, message, user)


@dp.callback_query(F.data == "open_profile")
async def handle_callback_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    if check_banned_user(user_id):
        await callback.answer("🚫 Аккаунт заблокирован.", show_alert=True)
        return

    await callback.answer("Загружаем профиль...")
    user = db.get_or_create_user(user_id, callback.from_user.username, callback.from_user.full_name or "Пользователь")
    await send_user_profile(user_id, callback.message, user)


async def send_user_profile(user_id: int, target_message: Message, user: dict):
    banner_buffer = create_profile_card(user)
    photo = BufferedInputFile(banner_buffer.getvalue(), filename=f"profile_{user_id}.png")

    status_badge = "⭐️ <b>PREMIUM PASS (БЕЗЛИМИТ)</b>" if user["is_premium"] else "⚡ <b>Базовый тариф (Free)</b>"
    q_info = "♾ <b>Безлимит</b>" if user["is_premium"] else f"<b>{user['queries_left']} из 2</b>"

    caption = (
        f"👤 <b>ЛИЧНЫЙ ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"• <b>Пользователь:</b> {user['full_name']} (@{user['username'] if user['username'] else 'нет'})\n"
        f"• <b>Telegram ID:</b> <code>{user['user_id']}</code>\n"
        f"• <b>Статус:</b> {status_badge}\n"
        f"• <b>Остаток проверок:</b> {q_info}\n"
        f"• <b>Всего выполнено проверок:</b> <b>{user['total_searches']}</b>\n"
        f"• <b>Дата регистрации:</b> {user['registered_at']}\n\n"
        f"{'💎 <i>У вас сняты все ограничения: любые юзернеймы без очереди.</i>' if user['is_premium'] else '💡 <i>Для безлимитного доступа активируйте Премиум или введите промокод.</i>'}"
    )

    await target_message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=profile_inline_keyboard(is_premium=bool(user["is_premium"]))
    )


# --------------------------------------------------------------------------
# 4. Manual Username Checking (User inputs ANY handle: «Поиск юзернейма»)
# --------------------------------------------------------------------------

@dp.message(F.text.in_([
    "🔍 Поиск юзернейма", "Поиск юзернейма", "🔍 Проверить юзернейм",
    "Проверить юзернейм", "🔍 Проверить юзернейм (ввести свой)", "🔍 Поиск", "Поиск",
    "Проверка", "Проверка юзернейма", "/check", "/search"
]))
@dp.callback_query(F.data.in_(["prompt_check_custom", "search_custom", "custom_check"]))
async def handle_prompt_custom_check(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    if check_banned_user(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("🚫 Аккаунт заблокирован.", show_alert=True)
        else:
            await event.answer("🚫 Аккаунт заблокирован.")
        return

    await state.set_state(Form.waiting_for_custom_username)
    text = (
        "🔎 <b>ПОИСК И ПРОВЕРКА ЮЗЕРНЕЙМА</b>\n\n"
        "Отправьте юзернейм, который вы хотите проверить (например: <code>@alex</code>, <code>vortex</code>, <code>crypto</code>):\n\n"
        "<i>Бот выполнит реальный аудит через Telegram и Fragment, определит доступность и рассчитает стоимость.</i>"
    )

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(text, parse_mode="HTML")
    else:
        await event.answer(text, parse_mode="HTML")


@dp.message(Form.waiting_for_custom_username)
async def handle_custom_username_input(message: Message, state: FSMContext):
    await state.clear()
    raw = message.text.strip().lstrip("@")
    await execute_username_audit(message, raw)


# Catch any text that looks like a username (starts with @ or is a 4-32 char tag)
@dp.message(F.text.regexp(r"^@?[a-zA-Z0-9_]{4,32}$"))
async def handle_direct_username_message(message: Message, state: FSMContext):
    await state.clear()
    raw = message.text.strip().lstrip("@")
    # Ignore commands or button labels
    if raw.startswith("/") or message.text in [
        "🔍 Поиск юзернейма", "Поиск юзернейма",
        "🔍 Проверить юзернейм (ввести свой)", 
        "⚡ Свободный юз (5 симв.)", 
        "✨ Свободный юз (6 симв.)", 
        "👤 Мой профиль", 
        "💎 Купить Премиум", 
        "ℹ️ О сервисе", "О сервисе",
        "📜 Меню и тарифы",
        "⚙️ Админ-панель"
    ]:
        return
    await execute_username_audit(message, raw)


async def execute_username_audit(message: Message, raw_username: str):
    user_id = message.from_user.id
    if check_banned_user(user_id):
        await message.answer("🚫 Аккаунт заблокирован.")
        return

    clean = raw_username.lower().strip()
    if len(clean) < 4:
        await message.answer("⚠️ Юзернейм должен содержать минимум 5 символов (4 символа продаются только на Fragment).")
        return

    # Check search quota
    if not db.can_search(user_id):
        await message.answer(
            "🛑 <b>Лимит запросов исчерпан!</b>\n\n"
            "На базовом тарифе доступно 2 бесплатные проверки. "
            "Чтобы проверять любые юзернеймы без ограничений, активируйте <b>Премиум</b>.",
            parse_mode="HTML",
            reply_markup=no_queries_left_inline_keyboard()
        )
        return

    db.consume_search(user_id)

    status_msg = await message.answer(
        f"⏳ <b>Проверяем юзернейм <code>@{clean}</code>...</b>\n"
        "• <i>Сканируем базу Telegram...</i>\n"
        "• <i>Проверяем аукцион Fragment...</i>\n"
        "• <i>Рассчитываем рыночную капитализацию...</i>",
        parse_mode="HTML"
    )

    try:
        res = await analyze_username(clean)
        val = res["valuation"]

        # Save to local DB & cloud
        db.save_found_username(user_id, clean, len(clean), val["ton"])
        asyncio.create_task(sync_search_to_cloud(user_id, clean, len(clean), val["ton"]))

        # Generate visual card
        card_buffer = create_username_card(clean, val, status_type=res["status_type"])
        photo = BufferedInputFile(card_buffer.getvalue(), filename=f"audit_{clean}.png")

        user = db.get_user(user_id)
        q_info = "⭐️ <b>БЕЗЛИМИТ</b>" if user["is_premium"] else f"<b>{user['queries_left']} из 2</b>"

        caption = (
            f"🔎 <b>РЕЗУЛЬТАТ ПРОВЕРКИ ЮЗЕРНЕЙМА:</b>\n\n"
            f"✨ <b>Тег:</b> <code>@{clean}</code>\n"
            f"📊 <b>Статус:</b> <b>{res['status_text']}</b>\n"
            f"ℹ️ <b>Инфо:</b> {res['details']}\n\n"
            f"💎 <b>Оценка стоимости:</b> ~<b>{val['ton']} TON</b> "
            f"(~${val['usd']} / ~{val['rub']:,} ₽)\n"
            f"🏆 <b>Редкость:</b> {val['tier']} {val['stars']}\n"
            f"🎵 <b>Гармония звучания:</b> {val['harmony']}%\n\n"
            f"📊 <i>Осталось запросов: {q_info}</i>"
        ).replace(",", " ")

        try:
            await status_msg.delete()
        except Exception:
            pass

        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=username_check_result_inline_keyboard(clean, res["is_free"], res["status_type"])
        )

    except Exception as e:
        logger.error(f"Error checking username: {e}", exc_info=True)
        await status_msg.edit_text("❌ Ошибка при проверке юзернейма. Попробуйте еще раз.")


# --------------------------------------------------------------------------
# 5. Verified Free 5- and 6-Character Handles Search
# --------------------------------------------------------------------------

@dp.message(F.text == "⚡ Свободный юз (5 симв.)")
@dp.callback_query(F.data == "search_len_5")
async def handle_search_free_5(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    await execute_free_search(event, 5)


@dp.message(F.text == "✨ Свободный юз (6 симв.)")
@dp.callback_query(F.data == "search_len_6")
async def handle_search_free_6(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    await execute_free_search(event, 6)


async def execute_free_search(event: Message | CallbackQuery, length: int):
    user_id = event.from_user.id
    if check_banned_user(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("🚫 Аккаунт заблокирован.", show_alert=True)
        else:
            await event.answer("🚫 Аккаунт заблокирован.")
        return

    if not db.can_search(user_id):
        msg_func = event.message.answer if isinstance(event, CallbackQuery) else event.answer
        if isinstance(event, CallbackQuery):
            await event.answer("Лимит исчерпан!", show_alert=True)
        await msg_func(
            "🛑 <b>Бесплатные запросы закончились!</b>\n\n"
            "Вы использовали свои 2 поиска. Перейдите на <b>Премиум</b>, "
            "чтобы получать проверенные свободные юзернеймы без ограничений.",
            parse_mode="HTML",
            reply_markup=no_queries_left_inline_keyboard()
        )
        return

    db.consume_search(user_id)

    if isinstance(event, CallbackQuery):
        await event.answer(f"Поиск свободного {length}-значного тега...")
        target_message = event.message
    else:
        target_message = event

    status_msg = await target_message.answer(
        f"⏳ <b>Подбираем свободный {length}-значный юзернейм...</b>\n"
        "• <i>Проверяем реальную доступность на Fragment и в Telegram...</i>\n"
        "• <i>Исключаем все занятые и выставленные на аукцион теги...</i>\n"
        "• <i>Генерируем дизайнерскую карточку...</i>",
        parse_mode="HTML"
    )

    try:
        username, val = await find_available_username(length)
        db.save_found_username(user_id, username, length, val["ton"])
        asyncio.create_task(sync_search_to_cloud(user_id, username, length, val["ton"]))

        card_buffer = create_username_card(username, val, status_type="FREE")
        photo = BufferedInputFile(card_buffer.getvalue(), filename=f"free_{username}.png")

        user = db.get_user(user_id)
        q_info = "⭐️ <b>БЕЗЛИМИТ</b>" if user["is_premium"] else f"<b>{user['queries_left']} из 2</b>"

        caption = (
            f"🎉 <b>НАЙДЕН ГАРАНТИРОВАННО СВОБОДНЫЙ ЮЗЕРНЕЙМ!</b>\n\n"
            f"✨ <b>Тег:</b> <code>@{username}</code>\n"
            f"✅ <b>Статус:</b> Свободен в Telegram прямо сейчас\n"
            f"📏 <b>Длина:</b> {length} символов\n"
            f"💎 <b>Оценка стоимости:</b> ~<b>{val['ton']} TON</b> "
            f"(~${val['usd']} / ~{val['rub']:,} ₽)\n"
            f"🏆 <b>Редкость:</b> {val['tier']} {val['stars']}\n"
            f"🎵 <b>Гармония звучания:</b> {val['harmony']}%\n\n"
            f"📊 <i>Осталось запросов: {q_info}</i>\n\n"
            f"👉 <i>Нажмите «Занять @{username}», чтобы зарезервировать его за собой!</i>"
        ).replace(",", " ")

        try:
            await status_msg.delete()
        except Exception:
            pass

        await target_message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=free_found_inline_keyboard(username, length)
        )

    except Exception as e:
        logger.error(f"Error during free search: {e}", exc_info=True)
        await status_msg.edit_text("❌ Ошибка при поиске. Попробуйте еще раз.")


# --------------------------------------------------------------------------
# 6. Premium Subscription & Promocodes
# --------------------------------------------------------------------------

@dp.message(F.text.in_(["💎 Купить Премиум", "Купить Премиум", "Премиум", "/premium"]))
@dp.callback_query(F.data == "open_premium")
async def handle_premium_offer(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    if check_banned_user(user_id):
        return

    user = db.get_or_create_user(user_id, event.from_user.username, event.from_user.full_name or "Пользователь")

    text = (
        "💎 <b>PREMIUM ПОДПИСКА — ПОЛНЫЙ БЕЗЛИМИТ</b>\n\n"
        "Стандартный аккаунт включает 2 бесплатных запроса. "
        "С подпиской <b>Премиум</b> вы получаете:\n\n"
        "• ♾ <b>Безлимитные проверки любых юзернеймов</b> 24/7\n"
        "• ⚡ Неограниченный доступ к базе свободных 5- и 6-значных тегов\n"
        "• 🎨 Скачивание карточек в Ultra HD\n"
        "• ⭐️ Золотой VIP бейдж в профиле\n\n"
        f"Текущий статус: {'⭐️ <b>У ВАС УЖЕ ЕСТЬ ПРЕМИУМ!</b>' if user['is_premium'] else '⚡ <b>Базовый доступ</b>'}\n\n"
        "👇 <i>Активируйте тестовый премиум в 1 клик или введите промокод:</i>"
    )

    await safe_edit_or_answer(event, text, reply_markup=premium_offer_inline_keyboard())


@dp.callback_query(F.data == "activate_demo_premium")
async def handle_activate_demo_premium(callback: CallbackQuery):
    user_id = callback.from_user.id
    if check_banned_user(user_id):
        return

    db.activate_premium(user_id)
    await callback.answer("⭐️ Премиум успешно активирован!", show_alert=True)
    user = db.get_user(user_id)
    asyncio.create_task(sync_user_to_cloud(
        user_id, user["username"], user["full_name"], 
        True, user["queries_left"], user["total_searches"]
    ))
    await send_user_profile(user_id, callback.message, user)


@dp.callback_query(F.data == "enter_promocode")
async def handle_promocode_prompt(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if check_banned_user(user_id):
        return

    await callback.answer()
    await state.set_state(Form.waiting_for_promocode)
    await callback.message.answer(
        "🎟 <b>Введите ваш промокод:</b>\n\n"
        "<i>Отправьте промокод ответным сообщением (например, <code>PREMIUM2026</code> или <code>VIPUSER</code>):</i>",
        parse_mode="HTML"
    )


@dp.message(Form.waiting_for_promocode)
async def handle_promocode_input(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if check_banned_user(user_id):
        return

    code = message.text.strip()
    success, msg = db.redeem_promocode(user_id, code)

    if success:
        user = db.get_user(user_id)
        asyncio.create_task(sync_user_to_cloud(
            user_id, user["username"], user["full_name"], 
            bool(user["is_premium"]), user["queries_left"], user["total_searches"]
        ))
        await message.answer(msg, parse_mode="HTML")
        await send_user_profile(user_id, message, user)
    else:
        await message.answer(
            f"{msg}\n\nПопробуйте ещё раз или обратитесь в поддержку.",
            parse_mode="HTML",
            reply_markup=profile_inline_keyboard()
        )


# --------------------------------------------------------------------------
# 7. History
# --------------------------------------------------------------------------

@dp.callback_query(F.data == "view_history")
async def handle_view_history(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    history = db.get_user_history(user_id, limit=6)

    if not history:
        await callback.message.answer(
            "📜 <b>История пуста.</b>\n\n"
            "Отправьте любой юзернейм в чат для проверки!",
            parse_mode="HTML",
            reply_markup=profile_inline_keyboard()
        )
        return

    lines = ["📜 <b>Ваши последние проверки и находки:</b>\n"]
    for i, h in enumerate(history, 1):
        lines.append(
            f"{i}. <code>@{h['username']}</code> — {h['length']} симв. "
            f"(~{h['valuation_ton']} TON) • <i>{h['created_at']}</i>"
        )

    await callback.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=profile_inline_keyboard())


# --------------------------------------------------------------------------
# 8. Admin Panel Handlers
# --------------------------------------------------------------------------

@dp.message(F.text.in_(["⚙️ Админ-панель", "Админ-панель", "/admin"]))
async def handle_admin_entry(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("⛔ <b>Доступ ограничен.</b> Вы не являетесь администратором бота.", parse_mode="HTML")
        return

    stats = db.get_admin_stats()
    text = (
        "👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ АДМИНИСТРАТОРА</b>\n\n"
        f"📊 <b>Быстрая статистика:</b>\n"
        f"• Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"• С подпиской Premium: <b>{stats['premium_users']}</b> ⭐️\n"
        f"• В бане: <b>{stats['banned_users']}</b> 🚫\n"
        f"• Всего проверок: <b>{stats['total_searches']}</b>\n"
        f"• Проверок сегодня: <b>{stats['searches_today']}</b>\n"
        f"• Активных промокодов: <b>{stats['active_promos']}</b>\n\n"
        "<i>Выберите раздел для управления:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=admin_main_keyboard())


@dp.callback_query(F.data == "adm_main")
async def handle_admin_main_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.answer("Доступ запрещён!", show_alert=True)
        return

    await callback.answer()
    stats = db.get_admin_stats()
    text = (
        "👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ АДМИНИСТРАТОРА</b>\n\n"
        f"📊 <b>Быстрая сводка:</b>\n"
        f"• Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"• С подпиской Premium: <b>{stats['premium_users']}</b> ⭐️\n"
        f"• В бане: <b>{stats['banned_users']}</b> 🚫\n"
        f"• Всего проверок: <b>{stats['total_searches']}</b>\n"
        f"• Проверок сегодня: <b>{stats['searches_today']}</b>\n"
        f"• Активных промокодов: <b>{stats['active_promos']}</b>\n\n"
        "<i>Выберите раздел:</i>"
    )
    await safe_edit_or_answer(callback, text, reply_markup=admin_main_keyboard())


@dp.callback_query(F.data == "adm_close")
async def handle_admin_close(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Админ-панель закрыта")
    try:
        await callback.message.delete()
    except Exception:
        pass


@dp.callback_query(F.data == "adm_stats")
async def handle_admin_detailed_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer()
    stats = db.get_admin_stats()
    text = (
        "📊 <b>ДЕТАЛЬНАЯ АНАЛИТИКА БОТА</b>\n\n"
        f"👥 <b>Пользователи:</b>\n"
        f"• Общая аудитория: <code>{stats['total_users']}</code> чел.\n"
        f"• Премиум-клиенты: <code>{stats['premium_users']}</code> чел. (конверсия: {round((stats['premium_users'] / max(1, stats['total_users'])) * 100, 1)}%)\n"
        f"• Заблокировано: <code>{stats['banned_users']}</code> чел.\n\n"
        f"🔍 <b>Активность проверок:</b>\n"
        f"• За всё время: <code>{stats['total_searches']}</code> проверок\n"
        f"• За сегодняшние сутки: <code>{stats['searches_today']}</code> находок\n\n"
        f"🎟 <b>Промокоды:</b>\n"
        f"• Неиспользованных кодов: <code>{stats['active_promos']}</code> шт.\n"
    )
    await safe_edit_or_answer(callback, text, reply_markup=admin_main_keyboard())


@dp.callback_query(F.data.startswith("adm_users_page_"))
async def handle_admin_users_pagination(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer()
    page = int(callback.data.split("_")[-1])
    users, total_pages, total_count = db.get_users_page(page=page, page_size=6)

    text = (
        f"👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b> (Всего: {total_count})\n\n"
        "<i>Нажмите на пользователя для просмотра профиля, бана или выдачи Премиума:</i>"
    )
    await safe_edit_or_answer(callback, text, reply_markup=admin_users_pagination_keyboard(users, page, total_pages))


@dp.callback_query(F.data.startswith("adm_u_"))
async def handle_admin_user_card(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    user = db.get_user(target_id)
    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    await callback.answer()
    await refresh_admin_user_card(callback, user)


async def refresh_admin_user_card(callback: CallbackQuery, user: dict):
    target_id = user["user_id"]
    banned_status = "🚫 <b>ЗАБАНЕН</b>" if user["is_banned"] else "🟢 <b>АКТИВЕН</b>"
    prem_status = "⭐️ <b>PREMIUM (Безлимит)</b>" if user["is_premium"] else "⚡ <b>Базовый (Free)</b>"
    q_left = "БЕЗЛИМИТ" if user["is_premium"] else f"{user['queries_left']} шт."

    text = (
        f"👤 <b>КАРТОЧКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"• <b>Telegram ID:</b> <code>{user['user_id']}</code>\n"
        f"• <b>Имя:</b> {user['full_name']}\n"
        f"• <b>Юзернейм:</b> @{user['username'] if user['username'] else 'нет'}\n"
        f"• <b>Статус:</b> {banned_status}\n"
        f"• <b>Подписка:</b> {prem_status}\n"
        f"• <b>Остаток запросов:</b> <code>{q_left}</code>\n"
        f"• <b>Всего проверок:</b> <code>{user['total_searches']}</code>\n"
        f"• <b>Дата регистрации:</b> {user['registered_at']}\n"
    )

    await safe_edit_or_answer(
        callback,
        text,
        reply_markup=admin_user_management_keyboard(
            target_id=target_id,
            is_banned=bool(user["is_banned"]),
            is_premium=bool(user["is_premium"])
        )
    )


@dp.callback_query(F.data.startswith("adm_action_ban_"))
async def handle_admin_action_ban(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    db.set_user_ban(target_id, True)
    await callback.answer("🚫 Пользователь заблокирован!", show_alert=True)
    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_action_unban_"))
async def handle_admin_action_unban(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    db.set_user_ban(target_id, False)
    await callback.answer("🟢 Пользователь разблокирован!", show_alert=True)
    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_action_prem_"))
async def handle_admin_action_prem(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    db.set_user_premium(target_id, True)
    await callback.answer("⭐️ Премиум успешно выдан!", show_alert=True)
    
    try:
        await bot.send_message(
            target_id, 
            "🎉 <b>Администратор выдал вам вечный PREMIUM доступ!</b>\n"
            "Все лимиты на проверки юзернеймов полностью сняты.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_action_unprem_"))
async def handle_admin_action_unprem(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    db.set_user_premium(target_id, False)
    await callback.answer("Премиум аннулирован.", show_alert=True)
    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_action_add5_"))
async def handle_admin_action_add5(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    new_q = db.add_user_queries(target_id, 5)
    await callback.answer(f"Начислено +5 запросов (стало {new_q})!", show_alert=True)
    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_action_add20_"))
async def handle_admin_action_add20(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    new_q = db.add_user_queries(target_id, 20)
    await callback.answer(f"Начислено +20 запросов (стало {new_q})!", show_alert=True)
    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_user_history_"))
async def handle_admin_user_history(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    history = db.get_user_history(target_id, limit=10)

    if not history:
        await callback.answer("У этого пользователя ещё нет проверок.", show_alert=True)
        return

    await callback.answer()
    lines = [f"📜 <b>Проверки пользователя <code>{target_id}</code>:</b>\n"]
    for i, h in enumerate(history, 1):
        lines.append(f"{i}. <code>@{h['username']}</code> ({h['length']}L, ~{h['valuation_ton']} TON) — {h['created_at']}")

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 К карточке пользователя", callback_data=f"adm_u_{target_id}")
    ]])
    await safe_edit_or_answer(callback, "\n".join(lines), reply_markup=kb)


@dp.callback_query(F.data == "adm_search_user")
async def handle_admin_search_user_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer()
    await state.set_state(Form.admin_waiting_search_user)
    await callback.message.answer(
        "🔎 <b>Поиск пользователя</b>\n\n"
        "Отправьте <b>Telegram ID</b> или <b>юзернейм</b> (например, <code>@username</code>):",
        parse_mode="HTML"
    )


@dp.message(Form.admin_waiting_search_user)
async def handle_admin_search_user_submit(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    query = message.text.strip()
    user = db.find_user_by_query(query)

    if not user:
        await message.answer(
            f"❌ Пользователь <code>{query}</code> не найден в базе.",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard()
        )
        return

    banned_status = "🚫 <b>ЗАБАНЕН</b>" if user["is_banned"] else "🟢 <b>АКТИВЕН</b>"
    prem_status = "⭐️ <b>PREMIUM</b>" if user["is_premium"] else "⚡ <b>Базовый (Free)</b>"
    q_left = "БЕЗЛИМИТ" if user["is_premium"] else f"{user['queries_left']} шт."

    text = (
        f"🎯 <b>РЕЗУЛЬТАТ ПОИСКА:</b>\n\n"
        f"• <b>Telegram ID:</b> <code>{user['user_id']}</code>\n"
        f"• <b>Имя:</b> {user['full_name']}\n"
        f"• <b>Юзернейм:</b> @{user['username'] if user['username'] else 'нет'}\n"
        f"• <b>Статус:</b> {banned_status}\n"
        f"• <b>Подписка:</b> {prem_status}\n"
        f"• <b>Остаток запросов:</b> <code>{q_left}</code>\n"
        f"• <b>Всего проверок:</b> <code>{user['total_searches']}</code>\n"
        f"• <b>Дата регистрации:</b> {user['registered_at']}\n"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_user_management_keyboard(
            target_id=user["user_id"],
            is_banned=bool(user["is_banned"]),
            is_premium=bool(user["is_premium"])
        )
    )


@dp.callback_query(F.data == "adm_broadcast")
async def handle_admin_broadcast_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer()
    await state.set_state(Form.admin_waiting_broadcast_message)
    total_users = len(db.get_all_user_ids())
    await callback.message.answer(
        f"📢 <b>МАССОВАЯ РАССЫЛКА</b> (Получателей: {total_users})\n\n"
        "Отправьте сообщение (текст, фото с текстом, стикер), которое будет разослано всем пользователям бота:",
        parse_mode="HTML"
    )


@dp.message(Form.admin_waiting_broadcast_message)
async def handle_admin_broadcast_preview(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(broadcast_message_id=message.message_id, broadcast_chat_id=message.chat.id)

    total_recipients = len(db.get_all_user_ids())
    await message.answer(
        f"👁 <b>Предпросмотр сообщения для рассылки выше.</b>\n\n"
        f"Всего получателей: <b>{total_recipients}</b> человек.\n"
        "Подтвердите отправку:",
        parse_mode="HTML",
        reply_markup=admin_broadcast_confirm_keyboard()
    )


@dp.callback_query(F.data == "adm_broadcast_confirm")
async def handle_admin_broadcast_execute(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    data = await state.get_data()
    await state.clear()
    await callback.answer()

    msg_id = data.get("broadcast_message_id")
    chat_id = data.get("broadcast_chat_id")

    if not msg_id:
        await callback.message.answer("❌ Ошибка: сообщение не найдено.")
        return

    user_ids = db.get_all_user_ids()
    progress_msg = await callback.message.answer(f"🚀 <b>Рассылка запущена...</b> (Всего: {len(user_ids)})", parse_mode="HTML")

    success_count = 0
    fail_count = 0

    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=chat_id,
                message_id=msg_id
            )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    await progress_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"• Успешно доставлено: <b>{success_count}</b>\n"
        f"• Заблокировали бота / недоступны: <b>{fail_count}</b>\n"
        f"• Всего обработано: <b>{len(user_ids)}</b>",
        parse_mode="HTML",
        reply_markup=admin_main_keyboard()
    )


@dp.callback_query(F.data == "adm_promos")
async def handle_admin_promos_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer()
    promos = db.get_all_promocodes()

    lines = ["🎟 <b>СПИСОК ПРОМОКОДОВ:</b>\n"]
    if not promos:
        lines.append("<i>Промокодов пока нет.</i>")
    else:
        for p in promos:
            status = f"❌ Использован (ID: {p['used_by']})" if p["is_used"] else "🟢 АКТИВЕН"
            lines.append(f"• <code>{p['code']}</code> — {status}")

    await safe_edit_or_answer(
        callback,
        "\n".join(lines),
        reply_markup=admin_promocodes_keyboard()
    )


@dp.callback_query(F.data == "adm_new_promo")
async def handle_admin_new_promo_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer()
    await state.set_state(Form.admin_waiting_new_promocode)
    await callback.message.answer(
        "🎟 <b>Создание промокода</b>\n\n"
        "Отправьте текст нового промокода (например, <code>SUPER2026</code>):",
        parse_mode="HTML"
    )


@dp.message(Form.admin_waiting_new_promocode)
async def handle_admin_new_promo_submit(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    code = message.text.strip().upper()

    if db.create_promocode(code):
        await message.answer(
            f"✅ Промокод <code>{code}</code> успешно создан и активен!\n"
            "При активации он выдает безлимитный Премиум.",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard()
        )
    else:
        await message.answer(
            f"⚠️ Промокод <code>{code}</code> уже существует в базе.",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard()
        )


@dp.callback_query(F.data == "adm_dump_db")
async def handle_admin_dump_db(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer("Подготовка базы данных...")
    if os.path.exists(DATABASE_PATH):
        doc = FSInputFile(DATABASE_PATH, filename="telegram_bot_database.sqlite3")
        await callback.message.answer_document(
            document=doc,
            caption="💾 <b>Резервная копия базы данных SQLite</b>",
            parse_mode="HTML"
        )
    else:
        await callback.message.answer("❌ Файл базы данных пока не создан.")


# --------------------------------------------------------------------------
# 9. Fallback & Smart Intent Handlers (Catch-all for resilient UX)
# --------------------------------------------------------------------------

@dp.message()
async def fallback_catch_all_message(message: Message, state: FSMContext):
    """
    Guarantees no user message is ever left unhandled.
    Detects user intent automatically.
    """
    raw = (message.text or "").strip()
    raw_lower = raw.lower()
    user_id = message.from_user.id
    logger.info(f"Fallback intent detector: '{raw}' from user {user_id}")

    if any(k in raw_lower for k in ["поиск", "провер", "найти", "check", "search", "тег", "юз"]):
        await handle_prompt_custom_check(message, state)
    elif any(k in raw_lower for k in ["сервис", "меню", "тариф", "инфо", "помощь", "о нас", "help", "about"]):
        await handle_service_info_menu(message, state)
    elif any(k in raw_lower for k in ["профил", "кабинет", "баланс", "аккаунт", "стат"]):
        await handle_profile(message, state)
    elif any(k in raw_lower for k in ["премиум", "купить", "безлимит", "vip", "подписк"]):
        await handle_premium_offer(message, state)
    elif len(raw) >= 4 and len(raw) <= 32 and " " not in raw and not raw.startswith("/"):
        await execute_username_audit(message, raw)
    else:
        await message.answer(
            "👋 <b>Главное меню:</b>\n"
            "Выберите нужное действие ниже или отправьте юзернейм для проверки (например: <code>@crypto</code>):",
            parse_mode="HTML",
            reply_markup=main_menu_reply_keyboard(is_admin=user_id in ADMIN_IDS)
        )


@dp.callback_query()
async def fallback_catch_all_callback(callback: CallbackQuery, state: FSMContext):
    """
    Catches any callback query from older messages or custom payloads.
    """
    data = (callback.data or "").lower()
    logger.info(f"Fallback intent callback: '{data}' from user {callback.from_user.id}")
    await callback.answer()

    if any(k in data for k in ["service", "info", "menu", "tariff", "about", "help"]):
        await handle_service_info_menu(callback, state)
    elif any(k in data for k in ["check", "search", "custom", "find"]):
        await handle_prompt_custom_check(callback, state)
    elif "profile" in data:
        await handle_callback_profile(callback, state)
    elif "prem" in data:
        await handle_premium_offer(callback, state)
    else:
        await handle_service_info_menu(callback, state)


# --------------------------------------------------------------------------
# Runner Entry Point
# --------------------------------------------------------------------------

async def main():
    db.init_db()
    logger.info("Initializing Telegram Username Radar Bot...")
    try:
        me = await bot.get_me()
        logger.info(f"Bot connected: @{me.username} ({me.first_name}) [ID: {me.id}]")
    except Exception as e:
        logger.error(f"Failed to verify bot: {e}")

    logger.info(f"Admin IDs registered: {ADMIN_IDS}")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

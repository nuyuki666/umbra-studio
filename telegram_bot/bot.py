"""
Telegram Username Radar Bot (aiogram 3.x)
High-performance async bot for finding available aesthetic 5- and 6-letter usernames,
evaluating market pricing, generating dynamic banners, managing premium subscriptions,
and providing a complete Admin Control Panel with User Inspection, Bans, Broadcasts, and Analytics.
"""
import os
import asyncio
import logging
from typing import Optional
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    CallbackQuery, 
    BufferedInputFile,
    FSInputFile
)

from config import BOT_TOKEN, ADMIN_IDS, DATABASE_PATH
import database as db
from generator import find_available_username
from card_builder import create_username_card, create_profile_card
from keyboards import (
    main_menu_reply_keyboard,
    length_choice_inline_keyboard,
    username_result_inline_keyboard,
    profile_inline_keyboard,
    premium_offer_inline_keyboard,
    no_queries_left_inline_keyboard,
    admin_main_keyboard,
    admin_users_pagination_keyboard,
    admin_user_management_keyboard,
    admin_broadcast_confirm_keyboard,
    admin_promocodes_keyboard
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# FSM States
class Form(StatesGroup):
    waiting_for_promocode = State()
    admin_waiting_search_user = State()
    admin_waiting_broadcast_message = State()
    admin_waiting_new_promocode = State()


dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)


# --------------------------------------------------------------------------
# Global Ban Check Helper
# --------------------------------------------------------------------------

def check_banned_user(user_id: int) -> bool:
    return db.is_user_banned(user_id)


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

    welcome_text = (
        f"👋 <b>Добро пожаловать, {full_name}!</b>\n\n"
        "⚡ <b>Telegram Username Radar</b> — профессиональный сервис поиска "
        "свободных, эстетичных и редких юзернеймов для вашего аккаунта или канала.\n\n"
        "✨ <b>Возможности сервиса:</b>\n"
        "• 🔍 Поиск свободных <b>5- и 6-символьных</b> юзернеймов\n"
        "• 📊 Оценка рыночной стоимости по стандартам Fragment (TON / USD / ₽)\n"
        "• 🎨 Генерация стильной дизайнерской карточки для каждого найденного юза\n"
        "• 👤 Личный профиль со статусом и статистикой\n\n"
        f"🎁 <b>Ваш тариф:</b> {'⭐️ <b>PREMIUM (Безлимит)</b>' if user['is_premium'] else f'⚡ <b>Базовый (2 бесплатных запроса)</b>'}\n"
        f"{'👑 <i>Вы авторизованы как администратор бота.</i>\n' if is_admin else ''}\n"
        "👇 <i>Выберите действие в меню ниже:</i>"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_reply_keyboard(is_admin=is_admin)
    )


# --------------------------------------------------------------------------
# 2. User Profile Handlers (Generates & Sends Profile Card Banner)
# --------------------------------------------------------------------------

@dp.message(F.text == "👤 Мой профиль")
@dp.message(Command("profile"))
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
        f"👤 <b>ЛИЧНЫЙ ПРОФИЛЬ</b>\n\n"
        f"• <b>Пользователь:</b> {user['full_name']} (@{user['username'] if user['username'] else 'нет'})\n"
        f"• <b>Telegram ID:</b> <code>{user['user_id']}</code>\n"
        f"• <b>Статус:</b> {status_badge}\n"
        f"• <b>Осталось поисков:</b> {q_info}\n"
        f"• <b>Всего выполнено поисков:</b> <b>{user['total_searches']}</b>\n"
        f"• <b>Дата регистрации:</b> {user['registered_at']}\n\n"
        f"{'💎 <i>У вас сняты все ограничения на поиск.</i>' if user['is_premium'] else '💡 <i>Для безлимитного поиска активируйте Премиум или введите промокод.</i>'}"
    )

    await target_message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=profile_inline_keyboard(is_premium=bool(user["is_premium"]))
    )


# --------------------------------------------------------------------------
# 3. Search & Length Selection Handlers
# --------------------------------------------------------------------------

@dp.message(F.text == "🔍 Поиск юзернейма")
@dp.message(Command("search"))
async def handle_search_menu(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if check_banned_user(user_id):
        await message.answer("🚫 Аккаунт заблокирован.")
        return

    user = db.get_or_create_user(user_id, message.from_user.username, message.from_user.full_name or "Пользователь")

    if not db.can_search(user_id):
        await message.answer(
            "⚠️ <b>Лимит бесплатных запросов исчерпан!</b>\n\n"
            "На базовом тарифе доступно 2 поиска. "
            "Чтобы искать без ограничений, подключите <b>Премиум (Безлимит)</b> или активируйте промокод.",
            parse_mode="HTML",
            reply_markup=no_queries_left_inline_keyboard()
        )
        return

    q_text = "♾ безлимит" if user["is_premium"] else f"{user['queries_left']} из 2"
    await message.answer(
        "🎯 <b>Выберите желаемую длину юзернейма:</b>\n\n"
        "• <b>5 символов</b> — Короткие, редкие, высокий спрос на Fragment\n"
        "• <b>6 символов</b> — Красивые, благозвучные и эстетичные теги\n\n"
        f"📊 <i>Ваш доступный лимит: {q_text}</i>",
        parse_mode="HTML",
        reply_markup=length_choice_inline_keyboard()
    )


@dp.callback_query(F.data == "menu_search")
async def handle_callback_menu_search(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    if check_banned_user(user_id):
        await callback.answer("🚫 Аккаунт заблокирован.", show_alert=True)
        return

    await callback.answer()
    user = db.get_or_create_user(user_id, callback.from_user.username, callback.from_user.full_name or "Пользователь")

    if not db.can_search(user_id):
        await callback.message.answer(
            "⚠️ <b>Лимит бесплатных запросов исчерпан!</b>\n\n"
            "Для снятия ограничений перейдите на Премиум.",
            parse_mode="HTML",
            reply_markup=no_queries_left_inline_keyboard()
        )
        return

    q_text = "♾ безлимит" if user["is_premium"] else f"{user['queries_left']} из 2"
    await callback.message.answer(
        "🎯 <b>Выберите желаемую длину юзернейма:</b>\n\n"
        "• <b>5 символов</b> — Редкие, короткие, высокий спрос\n"
        "• <b>6 символов</b> — Эстетичные и благозвучные теги\n\n"
        f"📊 <i>Осталось запросов: {q_text}</i>",
        parse_mode="HTML",
        reply_markup=length_choice_inline_keyboard()
    )


# --------------------------------------------------------------------------
# 4. Username Search Execution (5 or 6 characters)
# --------------------------------------------------------------------------

@dp.callback_query(F.data.in_(["search_len_5", "search_len_6"]))
async def handle_search_execute(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    if check_banned_user(user_id):
        await callback.answer("🚫 Аккаунт заблокирован.", show_alert=True)
        return

    length = 5 if callback.data == "search_len_5" else 6

    if not db.can_search(user_id):
        await callback.answer("Лимит запросов исчерпан!", show_alert=True)
        await callback.message.answer(
            "🛑 <b>Бесплатные запросы закончились!</b>\n\n"
            "Вы использовали свои 2 тестовых поиска. Перейдите на <b>Премиум</b>, "
            "чтобы искать свободные юзернеймы без ограничений.",
            parse_mode="HTML",
            reply_markup=no_queries_left_inline_keyboard()
        )
        return

    db.consume_search(user_id)
    await callback.answer(f"Поиск {length}-значного юзера...")

    status_msg = await callback.message.answer(
        f"⏳ <b>Ищем свободный юзернейм ({length} симв.)</b>...\n"
        "• <i>Проверяем занятость в сети Telegram...</i>\n"
        "• <i>Рассчитываем рыночную капитализацию...</i>\n"
        "• <i>Генерируем дизайнерскую карточку...</i>",
        parse_mode="HTML"
    )

    try:
        username, valuation = await find_available_username(length)
        db.save_found_username(user_id, username, length, valuation["ton"])

        card_buffer = create_username_card(username, valuation)
        photo = BufferedInputFile(card_buffer.getvalue(), filename=f"username_{username}.png")

        user = db.get_user(user_id)
        q_info = "⭐️ <b>БЕЗЛИМИТ</b>" if user["is_premium"] else f"<b>{user['queries_left']} из 2</b>"

        caption = (
            f"🎉 <b>НАЙДЕН СВОБОДНЫЙ ЮЗЕРНЕЙМ!</b>\n\n"
            f"✨ <b>Юзернейм:</b> <code>@{username}</code>\n"
            f"✅ <b>Статус:</b> Свободен в Telegram прямо сейчас\n"
            f"📏 <b>Длина:</b> {length} символов\n"
            f"💎 <b>Оценка стоимости:</b> ~<b>{valuation['ton']} TON</b> "
            f"(~${valuation['usd']} / ~{valuation['rub']:,} ₽)\n"
            f"🏆 <b>Редкость:</b> {valuation['tier']} {valuation['stars']}\n"
            f"🎵 <b>Гармония звучания:</b> {valuation['harmony']}%\n\n"
            f"📊 <i>Осталось запросов: {q_info}</i>\n\n"
            f"👉 <i>Нажмите «Занять @{username}», чтобы зарезервировать его за собой!</i>"
        ).replace(",", " ")

        try:
            await status_msg.delete()
        except Exception:
            pass

        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=username_result_inline_keyboard(username, length)
        )

    except Exception as e:
        logger.error(f"Error during username search: {e}", exc_info=True)
        await status_msg.edit_text("❌ Произошла ошибка при поиске. Попробуйте еще раз.")


# --------------------------------------------------------------------------
# 5. Premium Subscription & Promocodes
# --------------------------------------------------------------------------

@dp.message(F.text == "💎 Купить Премиум")
@dp.message(Command("premium"))
@dp.callback_query(F.data == "open_premium")
async def handle_premium_offer(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    if check_banned_user(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("🚫 Аккаунт заблокирован.", show_alert=True)
        else:
            await event.answer("🚫 Аккаунт заблокирован.")
        return

    user = db.get_or_create_user(user_id, event.from_user.username, event.from_user.full_name or "Пользователь")

    text = (
        "💎 <b>PREMIUM ПОДПИСКА — ПОЛНЫЙ БЕЗЛИМИТ</b>\n\n"
        "Стандартный аккаунт включает всего 2 запроса. "
        "С подпиской <b>Премиум</b> вы получаете абсолютную свободу:\n\n"
        "• ♾ <b>Безлимитное количество поисков</b> 24/7\n"
        "• ⚡ Мгновенная генерация 5- и 6-символьных юзернеймов\n"
        "• 🎨 Неограниченная загрузка дизайнерских карточек\n"
        "• ⭐️ Эксклюзивный статус и золотой бейдж в профиле\n\n"
        f"Текущий статус: {'⭐️ <b>У ВАС УЖЕ ЕСТЬ ПРЕМИУМ!</b>' if user['is_premium'] else '⚡ <b>Базовый доступ</b>'}\n\n"
        "👇 <i>Активируйте тестовый премиум в 1 клик или введите промокод:</i>"
    )

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(text, parse_mode="HTML", reply_markup=premium_offer_inline_keyboard())
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=premium_offer_inline_keyboard())


@dp.callback_query(F.data == "activate_demo_premium")
async def handle_activate_demo_premium(callback: CallbackQuery):
    user_id = callback.from_user.id
    if check_banned_user(user_id):
        await callback.answer("🚫 Аккаунт заблокирован.", show_alert=True)
        return

    db.activate_premium(user_id)
    await callback.answer("⭐️ Премиум успешно активирован!", show_alert=True)
    user = db.get_user(user_id)
    await send_user_profile(user_id, callback.message, user)


@dp.callback_query(F.data == "enter_promocode")
async def handle_promocode_prompt(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if check_banned_user(user_id):
        await callback.answer("🚫 Аккаунт заблокирован.", show_alert=True)
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
        await message.answer("🚫 Аккаунт заблокирован.")
        return

    code = message.text.strip()
    success, msg = db.redeem_promocode(user_id, code)

    if success:
        user = db.get_user(user_id)
        await message.answer(msg, parse_mode="HTML")
        await send_user_profile(user_id, message, user)
    else:
        await message.answer(
            f"{msg}\n\nПопробуйте ещё раз или обратитесь в поддержку.",
            parse_mode="HTML",
            reply_markup=profile_inline_keyboard()
        )


# --------------------------------------------------------------------------
# 6. History & Info Handlers
# --------------------------------------------------------------------------

@dp.callback_query(F.data == "view_history")
async def handle_view_history(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    history = db.get_user_history(user_id, limit=5)

    if not history:
        await callback.message.answer(
            "📜 <b>История находок пуста.</b>\n\n"
            "Вы пока не находили юзернеймы. Запустите поиск через меню!",
            parse_mode="HTML",
            reply_markup=length_choice_inline_keyboard()
        )
        return

    lines = ["📜 <b>Ваши последние найденные юзернеймы:</b>\n"]
    for i, h in enumerate(history, 1):
        lines.append(
            f"{i}. <code>@{h['username']}</code> — {h['length']} симв. "
            f"(~{h['valuation_ton']} TON) • <i>{h['created_at']}</i>"
        )

    await callback.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=profile_inline_keyboard())


@dp.message(F.text == "ℹ️ О сервисе")
@dp.message(Command("help"))
async def handle_help(message: Message):
    text = (
        "ℹ️ <b>О сервисе Telegram Username Radar</b>\n\n"
        "Бот создан для автоматического сканирования и генерации свободных "
        "эстетичных юзернеймов из 5 и 6 символов.\n\n"
        "• <b>Оценка стоимости</b> формируется на базе аналитики сделок на Fragment.com с учётом длины, благозвучия и редкости букв.\n"
        "• <b>Дизайнерская карточка</b> генерируется в высоком разрешении для каждого найденного юза.\n"
        "• <b>Тарифы:</b>\n"
        "  - Базовый: 2 бесплатных поиска\n"
        "  - Премиум: полный безлимит без ограничений\n\n"
        "Разработка и поддержка: @nuyuki666"
    )
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_reply_keyboard(is_admin=is_admin))


# --------------------------------------------------------------------------
# 7. Advanced Admin Panel Handlers
# --------------------------------------------------------------------------

@dp.message(F.text == "⚙️ Админ-панель")
@dp.message(Command("admin"))
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
        f"• Всего поисков: <b>{stats['total_searches']}</b>\n"
        f"• Поисков сегодня: <b>{stats['searches_today']}</b>\n"
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
        f"• Всего поисков: <b>{stats['total_searches']}</b>\n"
        f"• Поисков сегодня: <b>{stats['searches_today']}</b>\n"
        f"• Активных промокодов: <b>{stats['active_promos']}</b>\n\n"
        "<i>Выберите раздел:</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_main_keyboard())


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
        await callback.answer("Доступ запрещён!", show_alert=True)
        return

    await callback.answer()
    stats = db.get_admin_stats()
    text = (
        "📊 <b>ДЕТАЛЬНАЯ АНАЛИТИКА БОТА</b>\n\n"
        f"👥 <b>Пользователи:</b>\n"
        f"• Общая аудитория: <code>{stats['total_users']}</code> чел.\n"
        f"• Премиум-клиенты: <code>{stats['premium_users']}</code> чел. (конверсия: {round((stats['premium_users'] / max(1, stats['total_users'])) * 100, 1)}%)\n"
        f"• Заблокировано: <code>{stats['banned_users']}</code> чел.\n\n"
        f"🔍 <b>Активность поисков:</b>\n"
        f"• За всё время: <code>{stats['total_searches']}</code> проверок\n"
        f"• За сегодняшние сутки: <code>{stats['searches_today']}</code> находок\n\n"
        f"🎟 <b>Промокоды:</b>\n"
        f"• Неиспользованных кодов: <code>{stats['active_promos']}</code> шт.\n"
    )
    await callback.message.edit_text(
        text, 
        parse_mode="HTML", 
        reply_markup=admin_main_keyboard()
    )


# --------------------------------------------------------------------------
# Admin: User Inspection & Pagination
# --------------------------------------------------------------------------

@dp.callback_query(F.data.startswith("adm_users_page_"))
async def handle_admin_users_pagination(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещён!", show_alert=True)
        return

    await callback.answer()
    page = int(callback.data.split("_")[-1])
    users, total_pages, total_count = db.get_users_page(page=page, page_size=6)

    text = (
        f"👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b> (Всего: {total_count})\n\n"
        "<i>Нажмите на пользователя для просмотра профиля, бана или выдачи Премиума:</i>"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_users_pagination_keyboard(users, page, total_pages)
    )


@dp.callback_query(F.data.startswith("adm_u_"))
async def handle_admin_user_card(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещён!", show_alert=True)
        return

    target_id = int(callback.data.split("_")[-1])
    user = db.get_user(target_id)
    if not user:
        await callback.answer("Пользователь не найден!", show_alert=True)
        return

    await callback.answer()
    banned_status = "🚫 <b>ЗАБАНЕН</b>" if user["is_banned"] else "🟢 <b>АКТИВЕН</b>"
    prem_status = "⭐️ <b>PREMIUM (Безлимит)</b>" if user["is_premium"] else "⚡ <b>Базовый (Free)</b>"
    q_left = "БЕЗЛИМИТ" if user["is_premium"] else f"{user['queries_left']} шт."

    text = (
        f"👤 <b>КАРТОЧКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"• <b>Telegram ID:</b> <code>{user['user_id']}</code>\n"
        f"• <b>Имя:</b> {user['full_name']}\n"
        f"• <b>Юзернейм:</b> @{user['username'] if user['username'] else 'нет'}\n"
        f"• <b>Статус аккаунта:</b> {banned_status}\n"
        f"• <b>Подписка:</b> {prem_status}\n"
        f"• <b>Остаток запросов:</b> <code>{q_left}</code>\n"
        f"• <b>Всего выполнено поисков:</b> <code>{user['total_searches']}</code>\n"
        f"• <b>Дата регистрации:</b> {user['registered_at']}\n"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_user_management_keyboard(
            target_id=target_id,
            is_banned=bool(user["is_banned"]),
            is_premium=bool(user["is_premium"])
        )
    )


# --------------------------------------------------------------------------
# Admin: User Actions (Ban / Unban / Premium / Add Queries)
# --------------------------------------------------------------------------

@dp.callback_query(F.data.startswith("adm_action_ban_"))
async def handle_admin_action_ban(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    db.set_user_ban(target_id, True)
    await callback.answer("🚫 Пользователь заблокирован!", show_alert=True)
    # Refresh card
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
    
    # Notify target user
    try:
        await bot.send_message(
            target_id, 
            "🎉 <b>Администратор выдал вам вечный PREMIUM доступ!</b>\n"
            "Все лимиты на поиск юзернеймов полностью сняты. Приятного использования!",
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
    
    try:
        await bot.send_message(
            target_id, 
            "🎁 <b>Администратор начислил вам +5 бонусных запросов на поиск!</b>", 
            parse_mode="HTML"
        )
    except Exception:
        pass

    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_action_add20_"))
async def handle_admin_action_add20(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    new_q = db.add_user_queries(target_id, 20)
    await callback.answer(f"Начислено +20 запросов (стало {new_q})!", show_alert=True)
    
    try:
        await bot.send_message(
            target_id, 
            "🎁 <b>Администратор начислил вам +20 бонусных запросов на поиск!</b>", 
            parse_mode="HTML"
        )
    except Exception:
        pass

    user = db.get_user(target_id)
    await refresh_admin_user_card(callback, user)


@dp.callback_query(F.data.startswith("adm_user_history_"))
async def handle_admin_user_history(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    target_id = int(callback.data.split("_")[-1])
    history = db.get_user_history(target_id, limit=10)

    if not history:
        await callback.answer("У этого пользователя ещё нет находок.", show_alert=True)
        return

    await callback.answer()
    lines = [f"📜 <b>Находки пользователя <code>{target_id}</code>:</b>\n"]
    for i, h in enumerate(history, 1):
        lines.append(f"{i}. <code>@{h['username']}</code> ({h['length']}L, ~{h['valuation_ton']} TON) — {h['created_at']}")

    lines.append("\n<i>Нажмите Назад для возврата к пользователю:</i>")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 К карточке пользователя", callback_data=f"adm_u_{target_id}")
    ]])
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)


async def refresh_admin_user_card(callback: CallbackQuery, user: dict):
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
        f"• <b>Всего выполнено поисков:</b> <code>{user['total_searches']}</code>\n"
        f"• <b>Дата регистрации:</b> {user['registered_at']}\n"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_user_management_keyboard(
            target_id=user["user_id"],
            is_banned=bool(user["is_banned"]),
            is_premium=bool(user["is_premium"])
        )
    )


# --------------------------------------------------------------------------
# Admin: Search User by ID or @username
# --------------------------------------------------------------------------

@dp.callback_query(F.data == "adm_search_user")
async def handle_admin_search_user_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.answer()
    await state.set_state(Form.admin_waiting_search_user)
    await callback.message.answer(
        "🔎 <b>Поиск пользователя</b>\n\n"
        "Отправьте <b>Telegram ID</b> (цифры) или <b>юзернейм</b> (например, <code>@username</code>):",
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
            f"❌ Пользователь по запросу <code>{query}</code> не найден в базе данных.",
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
        f"• <b>Всего поисков:</b> <code>{user['total_searches']}</code>\n"
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


# --------------------------------------------------------------------------
# Admin: Mass Broadcast to All Users
# --------------------------------------------------------------------------

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
            await asyncio.sleep(0.05)  # Flood protection rate-limiting
        except Exception:
            fail_count += 1

    await progress_msg.edit_text(
        f"✅ <b>Рассылка успешно завершена!</b>\n\n"
        f"• Успешно доставлено: <b>{success_count}</b>\n"
        f"• Заблокировали бота / недоступны: <b>{fail_count}</b>\n"
        f"• Всего обработано: <b>{len(user_ids)}</b>",
        parse_mode="HTML",
        reply_markup=admin_main_keyboard()
    )


# --------------------------------------------------------------------------
# Admin: Promo Codes Management & Database Backup
# --------------------------------------------------------------------------

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

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
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
        "Отправьте текст нового промокода (например, <code>SUPER2026</code> или <code>SUMMERVIP</code>):",
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

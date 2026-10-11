"""
Telegram Username Radar Bot (aiogram 3.x)
High-performance async bot for finding available aesthetic 5- and 6-letter usernames,
evaluating market pricing, generating dynamic banners, and managing premium subscriptions.
"""
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    CallbackQuery, 
    BufferedInputFile
)

from config import BOT_TOKEN
import database as db
from generator import find_available_username
from card_builder import create_username_card, create_profile_card
from keyboards import (
    main_menu_reply_keyboard,
    length_choice_inline_keyboard,
    username_result_inline_keyboard,
    profile_inline_keyboard,
    premium_offer_inline_keyboard,
    no_queries_left_inline_keyboard
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# FSM States
class Form(StatesGroup):
    waiting_for_promocode = State()


dp = Dispatcher()


# --------------------------------------------------------------------------
# 1. /start & Welcome Handlers
# --------------------------------------------------------------------------

@dp.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name or "Пользователь"

    user = db.get_or_create_user(user_id, username, full_name)

    welcome_text = (
        f"👋 <b>Добро пожаловать, {full_name}!</b>\n\n"
        "⚡ <b>Telegram Username Radar</b> — профессиональный сервис поиска "
        "свободных, эстетичных и ценных юзернеймов для вашего аккаунта или канала.\n\n"
        "✨ <b>Что умеет бот:</b>\n"
        "• 🔍 Поиск свободных <b>5- и 6-символьных</b> юзернеймов\n"
        "• 📊 Оценка рыночной стоимости по стандартам Fragment (TON / USD / ₽)\n"
        "• 🎨 Генерация стильной карточки с дизайном каждого найденного юза\n"
        "• 👤 Личный профиль со статистикой и статусом\n\n"
        f"🎁 <b>Ваш тариф:</b> {'⭐️ <b>PREMIUM (Безлимит)</b>' if user['is_premium'] else f'⚡ <b>Базовый (2 бесплатных запроса)</b>'}\n\n"
        "👇 <i>Выберите действие в меню ниже:</i>"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_reply_keyboard()
    )


# --------------------------------------------------------------------------
# 2. User Profile Handlers (Generates & Sends Profile Card Banner)
# --------------------------------------------------------------------------

@dp.message(F.text == "👤 Мой профиль")
@dp.message(Command("profile"))
async def handle_profile(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = db.get_or_create_user(user_id, message.from_user.username, message.from_user.full_name or "Пользователь")
    await send_user_profile(user_id, message, user)


@dp.callback_query(F.data == "open_profile")
async def handle_callback_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Загружаем профиль...")
    user_id = callback.from_user.id
    user = db.get_or_create_user(user_id, callback.from_user.username, callback.from_user.full_name or "Пользователь")
    await send_user_profile(user_id, callback.message, user)


async def send_user_profile(user_id: int, target_message: Message, user: dict):
    # 1. Generate customized visual profile card banner using Pillow
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
    user = db.get_or_create_user(user_id, message.from_user.username, message.from_user.full_name or "Пользователь")

    if not db.can_search(user_id):
        await message.answer(
            "⚠️ <b>Лимит бесплатных запросов исчерпан!</b>\n\n"
            "На базовом тарифе доступно только 2 поиска. "
            "Чтобы искать без ограничений, подключите <b>Премиум (Безлимит)</b> или активируйте промокод.",
            parse_mode="HTML",
            reply_markup=no_queries_left_inline_keyboard()
        )
        return

    q_text = "♾ безлимит" if user["is_premium"] else f"{user['queries_left']} из 2"
    await message.answer(
        "🎯 <b>Выберите желаемую длину юзернейма:</b>\n\n"
        "• <b>5 символов</b> — Редкие, дорогие, высокий спрос на аукционе Fragment\n"
        "• <b>6 символов</b> — Красивые, гармоничные и благозвучные теги\n\n"
        f"📊 <i>Ваш доступный лимит: {q_text}</i>",
        parse_mode="HTML",
        reply_markup=length_choice_inline_keyboard()
    )


@dp.callback_query(F.data == "menu_search")
async def handle_callback_menu_search(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id
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
    length = 5 if callback.data == "search_len_5" else 6

    # 1. Check queries left
    if not db.can_search(user_id):
        await callback.answer("Лимит запросов исчерпан!", show_alert=True)
        await callback.message.answer(
            "🛑 <b>Бесплатные запросы закончились!</b>\n\n"
            "Вы использовали свои 2 тестовых поиска. Перейдите на <b>Премиум</b>, "
            "чтобы искать свободные юзернеймы без каких-либо ограничений.",
            parse_mode="HTML",
            reply_markup=no_queries_left_inline_keyboard()
        )
        return

    # Consume query
    db.consume_search(user_id)
    await callback.answer(f"Поиск {length}-значного юзера...")

    status_msg = await callback.message.answer(
        f"⏳ <b>Ищем красивый свободный юзернейм ({length} симв.)</b>...\n"
        "• <i>Проверяем занятость в сети Telegram...</i>\n"
        "• <i>Рассчитываем рыночную капитализацию...</i>\n"
        "• <i>Генерируем дизайнерскую карточку...</i>",
        parse_mode="HTML"
    )

    try:
        # 2. Generator finds available username and calculates valuation
        username, valuation = await find_available_username(length)

        # Save to database history
        db.save_found_username(user_id, username, length, valuation["ton"])

        # 3. Build aesthetic high-res Pillow card
        card_buffer = create_username_card(username, valuation)
        photo = BufferedInputFile(card_buffer.getvalue(), filename=f"username_{username}.png")

        # 4. User updated data
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

        # Delete waiting status and send card
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
    db.activate_premium(user_id)
    await callback.answer("⭐️ Премиум успешно активирован!", show_alert=True)
    user = db.get_user(user_id)
    await send_user_profile(user_id, callback.message, user)


@dp.callback_query(F.data == "enter_promocode")
async def handle_promocode_prompt(callback: CallbackQuery, state: FSMContext):
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
    code = message.text.strip()
    user_id = message.from_user.id

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
        "• <b>Оценка стоимости</b> формируется на базе открытой аналитики сделок на Fragment.com с учётом длины, благозвучия и редкости букв.\n"
        "• <b>Карточка</b> визуализирует ключевые метрики тега для удобной оценки или перепродажи.\n"
        "• <b>Лимиты:</b>\n"
        "  - Базовый: 2 бесплатных поиска\n"
        "  - Премиум: полный безлимит без ограничений\n\n"
        "Связь и идеи: @nuyuki666"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_reply_keyboard())


# --------------------------------------------------------------------------
# 7. Runner Entry Point
# --------------------------------------------------------------------------

async def main():
    db.init_db()
    token = os.getenv("BOT_TOKEN") or BOT_TOKEN

    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "=" * 60)
        print("⚠️  ВНИМАНИЕ: BOT_TOKEN не указан!")
        print("1. Получите токен у @BotFather в Telegram.")
        print("2. Укажите его в config.py или в переменной окружения BOT_TOKEN.")
        print("=" * 60 + "\n")

    bot = Bot(token=token)
    logger.info("Bot starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

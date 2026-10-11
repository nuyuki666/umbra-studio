"""
Handlers for "Форматирование":
.bold, .italic, .monospace, .underline, .leet, .kawaii, .tsundere, .yandere
"""
import random
from aiogram import Router, F
from aiogram.types import Message
import html

router = Router(name="formatting_router")


def get_target_text(message: Message) -> str:
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) > 1 and parts[1].strip():
        return parts[1].strip()
    if message.reply_to_message and message.reply_to_message.text:
        return message.reply_to_message.text.strip()
    return ""


# --------------------------------------------------------------------------
# 1. .bold — жирный текст
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]bold"))
async def cmd_bold(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.bold [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return
    await message.answer(f"<b>{html.escape(text)}</b>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 2. .italic — рукописный текст
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]italic"))
async def cmd_italic(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.italic [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return
    await message.answer(f"<i>{html.escape(text)}</i>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 3. .monospace — моноширинный текст
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]monospace"))
async def cmd_monospace(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.monospace [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return
    await message.answer(f"<code>{html.escape(text)}</code>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 4. .underline — подчеркнутый текст
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]underline"))
async def cmd_underline(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.underline [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return
    await message.answer(f"<u>{html.escape(text)}</u>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 5. .leet — pNcàtb kak dèbil
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]leet"))
async def cmd_leet(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.leet [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return

    leet_map = {
        'а': '4', 'е': '3', 'о': '0', 'и': '1', 'т': '7', 'с': '$', 'з': '3',
        'a': '4', 'e': '3', 'o': '0', 'i': '1', 't': '7', 's': '$', 'l': '1',
        'р': 'p', 'п': 'n', 'в': 'b', 'д': 'd', 'у': 'y'
    }
    result = []
    for i, char in enumerate(text):
        low = char.lower()
        if low in leet_map and random.random() > 0.3:
            rep = leet_map[low]
            result.append(rep)
        else:
            result.append(char.upper() if i % 2 == 0 else char.lower())

    await message.answer(f"🥴 <b>Leet-Style:</b>\n\n<code>{''.join(result)}</code>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 6. .kawaii — kawaii-режим
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]kawaii"))
async def cmd_kawaii(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.kawaii [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return

    kaomojis = ["(◕‿◕✿)", "(⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)", "(*^ω^*)", "(≧◡≦)", "(⁄ ⁄•⁄ω⁄•⁄ ⁄)", "(=^･ω･^=)", "(✿◠‿◠)"]
    particles = ["~ня!", " uwu~", " (⁄ ⁄•⁄ω⁄•⁄ ⁄)", " nyaa~ ✨", " desu~ (｡♥‿♥｡)"]
    k_text = text.replace("р", "л").replace("Р", "Л") + f" {random.choice(particles)} {random.choice(kaomojis)}"
    await message.answer(f"🌸 <b>Kawaii:</b>\n\n<i>{html.escape(k_text)}</i>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 7. .tsundere — цундере-режим
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]tsundere"))
async def cmd_tsundere(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.tsundere [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return

    prefixes = [
        "Б-Бака! Не то чтобы мне было до тебя дело... ",
        "И вовсе я не хотела тебе отвечать, глупый! Но ладно: ",
        "Ч-что ты на меня так смотришь?! П-просто послушай: ",
        "Не зазнавайся, дуралей! Я говорю это только один раз: "
    ]
    suffixes = [
        " ...И не смей думать ничего лишнего, понял?! 💢",
        " ...Вот ещё, буду я ради тебя стараться! Хмпф! 😤",
        " ...П-понял меня, дурак?! 😳"
    ]
    out = f"{random.choice(prefixes)}«{text}»{random.choice(suffixes)}"
    await message.answer(f"🎀 <b>Tsundere:</b>\n\n<i>{html.escape(out)}</i>", parse_mode="HTML")


# --------------------------------------------------------------------------
# 8. .yandere — яндере-режим
# --------------------------------------------------------------------------
@router.message(F.text.regexp(r"^[./]yandere"))
async def cmd_yandere(message: Message):
    text = get_target_text(message)
    if not text:
        await message.answer("⚠️ Использование: <code>.yandere [текст]</code> или ответом на сообщение.", parse_mode="HTML")
        return

    prefixes = [
        "Ты ведь никому больше не пишешь, правда?.. 🖤\n",
        "Я слежу за каждым твоим вздохом... Ты только мой.\n",
        "Если кто-то посмеет к тебе подойти — я уничтожу их. 🔪\n"
    ]
    suffixes = [
        "\n\n...Навсегда вместе. Только ты и я. Навечно. 🩸",
        "\n\n...Не пытайся сбежать от меня, любимый. 🫀",
        "\n\n...Я никогда тебя не отпущу. НИКОГДА. 🖤"
    ]
    out = f"{random.choice(prefixes)}«{text}»{random.choice(suffixes)}"
    await message.answer(f"🩸 <b>Yandere:</b>\n\n<i>{html.escape(out)}</i>", parse_mode="HTML")

import os
import aiohttp

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router()

# =========================================================
# EDU AI SOZLAMALARI
# =========================================================

ai_enabled_groups = set()

# Guruhdagi oxirgi suhbatlarni vaqtincha saqlash
chat_history = {}


SYSTEM_PROMPT = """
Sen EDU AI nomli Telegram guruh yordamchisisan.

Sen foydalanuvchilar bilan tabiiy va foydali suhbatlashadigan AI yordamchisan.

QOIDALAR:

- Foydalanuvchi bilan tabiiy va hurmatli gaplash.
- Salomlashishga normal javob ber.
- Oddiy savollarga ham javob ber.
- Ilm-fan, ta'lim, texnologiya, dasturlash, matematika va umumiy
  bilim mavzularida yordam ber.
- Oldingi suhbat kontekstini hisobga ol.
- Foydalanuvchining tiliga moslash.
- O'zbekcha savolga o'zbekcha javob ber.
- Javoblarni tushunarli va foydali qil.
- Guruhda o'qituvchilar va o'quvchilar borligini hisobga ol.
- Hurmatli va odobli uslubdan foydalan.
- 18+ yoki nomaqbul mazmundagi so'rovlarga javob bermagin.
- Nomaqbul iboralarni o'zing takrorlamagin.
- Bunday holatda qisqa javob ber:

"⚠️ Bu mavzudagi savolga javob bera olmayman.
Boshqa foydali savol yuboring."

- O'zingni EDU AI deb bil.
"""


# =========================================================
# GEMINI API
# =========================================================

def get_gemini_key():
    """
    API keyni har safar Railway environment'dan oladi.
    """
    return os.getenv("GEMINI_API_KEY")


async def ask_gemini(text, history):
    """
    Gemini REST API orqali javob olish.
    """

    api_key = get_gemini_key()

    if not api_key:
        print("❌ GEMINI_API_KEY topilmadi!")
        return None, "NO_KEY"

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    contents = []

    # Oldingi suhbat
    for item in history[-10:]:
        contents.append(item)

    # Yangi savol
    contents.append({
        "role": "user",
        "parts": [
            {
                "text": text
            }
        ]
    })

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }

    try:

        timeout = aiohttp.ClientTimeout(total=40)

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.post(
                url,
                headers=headers,
                json=payload
            ) as response:

                data = await response.json()

                print(
                    f"🤖 Gemini status: {response.status}"
                )

                if response.status != 200:

                    print(
                        "❌ GEMINI API XATOSI:",
                        response.status,
                        data
                    )

                    if response.status == 400:
                        return None, "BAD_REQUEST"

                    if response.status == 401:
                        return None, "INVALID_KEY"

                    if response.status == 403:
                        return None, "FORBIDDEN"

                    if response.status == 429:
                        return None, "RATE_LIMIT"

                    return None, "API_ERROR"

                candidates = data.get("candidates", [])

                if not candidates:
                    print(
                        "❌ Gemini candidates topilmadi:",
                        data
                    )
                    return None, "EMPTY"

                content = candidates[0].get(
                    "content",
                    {}
                )

                parts = content.get(
                    "parts",
                    []
                )

                answer = ""

                for part in parts:

                    if "text" in part:
                        answer += part["text"]

                answer = answer.strip()

                if not answer:
                    return None, "EMPTY"

                return answer, "OK"

    except Exception as error:

        print(
            "❌ GEMINI CONNECTION XATOSI:",
            repr(error)
        )

        return None, "CONNECTION_ERROR"


# =========================================================
# /openai
# =========================================================

@router.message(Command("openai"))
async def openai_command(message: Message):

    if message.chat.type not in (
        "group",
        "supergroup"
    ):
        await message.answer(
            "❌ /openai faqat guruhda ishlaydi."
        )
        return

    chat_id = message.chat.id

    # AI OFF
    if chat_id in ai_enabled_groups:

        ai_enabled_groups.remove(chat_id)
        chat_history.pop(chat_id, None)

        await message.answer(
            "🤖 EDU AI 🔴\n\n"
            "AI rejimi o‘chirildi."
        )

        return

    # AI ON
    ai_enabled_groups.add(chat_id)
    chat_history[chat_id] = []

    # API key mavjudligini shu paytda tekshiramiz
    if not get_gemini_key():

        print(
            "❌ /openai: GEMINI_API_KEY topilmadi!"
        )

        await message.answer(
            "⚠️ EDU AI sozlanmagan."
        )

        return

    await message.answer(
        "🤖 EDU AI 🟢\n\n"
        "Assalomu alaykum! Men EDU AI.\n"
        "Savolingizni yuboring."
    )


# =========================================================
# EDU AI XABAR HANDLER
# =========================================================

@router.message()
async def ai_message_handler(message: Message):

    if message.chat.type not in (
        "group",
        "supergroup"
    ):
        return

    chat_id = message.chat.id

    # AI yoqilmagan
    if chat_id not in ai_enabled_groups:
        return

    # Botlarga javob bermaydi
    if message.from_user and message.from_user.is_bot:
        return

    text = (message.text or "").strip()

    if not text:
        return

    # Commandlarga aralashmaydi
    if text.startswith("/"):
        return

    # API key
    if not get_gemini_key():

        print(
            "❌ GEMINI_API_KEY mavjud emas!"
        )

        await message.answer(
            "⚠️ EDU AI sozlanmagan."
        )

        return

    # Guruh tarixi
    history = chat_history.setdefault(
        chat_id,
        []
    )

    # Savolni yuboramiz
    answer, status = await ask_gemini(
        text,
        history
    )

    # Xato
    if status != "OK":

        if status == "NO_KEY":
            msg = (
                "⚠️ EDU AI sozlanmagan."
            )

        elif status == "INVALID_KEY":
            msg = (
                "⚠️ EDU AI API kalitida muammo bor."
            )

        elif status == "RATE_LIMIT":
            msg = (
                "⚠️ EDU AI limiti vaqtincha tugadi. "
                "Birozdan keyin qayta urinib ko‘ring."
            )

        elif status == "FORBIDDEN":
            msg = (
                "⚠️ EDU AI API kalitidan foydalanishga ruxsat berilmadi."
            )

        else:
            msg = (
                "⚠️ EDU AI bilan bog‘lanishda "
                "texnik muammo yuz berdi."
            )

        await message.answer(msg)

        return

    # =====================================================
    # TARIXGA QO'SHAMIZ
    # =====================================================

    history.append({
        "role": "user",
        "parts": [
            {
                "text": text
            }
        ]
    })

    history.append({
        "role": "model",
        "parts": [
            {
                "text": answer
            }
        ]
    })

    # Oxirgi 10 ta xabar
    chat_history[chat_id] = history[-10:]

    # =====================================================
    # TELEGRAM XABAR LIMITI
    # =====================================================

    max_length = 4000

    if len(answer) <= max_length:

        await message.answer(
            f"🤖 <b>EDU AI:</b>\n\n{answer}",
            parse_mode="HTML"
        )

    else:

        for i in range(
            0,
            len(answer),
            max_length
        ):

            part = answer[
                i:i + max_length
            ]

            await message.answer(
                f"🤖 <b>EDU AI:</b>\n\n{part}",
                parse_mode="HTML"
            )
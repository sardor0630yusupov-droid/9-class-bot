import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from openai import AsyncOpenAI


router = Router()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("⚠️ OPENAI_API_KEY topilmadi!")

client = AsyncOpenAI(api_key=api_key) if api_key else None

# Qaysi guruhlarda AI yoqilganini saqlaydi
ai_enabled_groups = set()

SYSTEM_PROMPT = """
Sen EDU AI nomli Telegram guruh yordamchisisan.

Sening vazifang:
- Faqat foydali savollarga javob berish.
- Ilmiy, ta'limiy, texnologik va umumiy foydali savollarga tushunarli javob berish.
- Oddiy hol-ahvol yoki keraksiz suhbatni davom ettirmaslik.
- 18+ yoki nomaqbul mazmundagi so'rovlarga javob bermaslik.
- Nomaqbul iboralarni javobingda takrorlamaslik.
- Bunday holatda faqat:
  "⚠️ Bu mavzudagi savollarga javob bera olmayman. Iltimos, ilmiy, ta'limiy yoki foydali savol yuboring."
  mazmunida qisqa javob berish.
- O'zbek tilida berilgan savollarga o'zbek tilida javob ber.
- Javoblarni qisqa, aniq va tushunarli qil.
- O'zingni EDU AI deb tanishtir.
"""


@router.message(Command("openai"))
async def openai_command(message: Message):
    # Faqat guruhda
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(
            "❌ /openai faqat guruhda ishlaydi."
        )
        return

    chat_id = message.chat.id

    # ON/OFF
    if chat_id in ai_enabled_groups:
        ai_enabled_groups.remove(chat_id)

        await message.answer(
            "🤖 <b>EDU AI</b> 🔴\n\n"
            "AI suhbat rejimi o‘chirildi.",
            parse_mode="HTML"
        )
        return

    ai_enabled_groups.add(chat_id)

    await message.answer(
        "🤖 <b>Assalomu alaykum! Men EDU AI.</b>\n\n"
        "Savolingizni yuboring.",
        parse_mode="HTML"
    )


@router.message()
async def ai_message_handler(message: Message):
    # Faqat guruh
    if message.chat.type not in ("group", "supergroup"):
        return

    # AI yoqilmagan bo'lsa jim turadi
    if message.chat.id not in ai_enabled_groups:
        return

    # Botlarning xabarlariga javob bermaydi
    if message.from_user and message.from_user.is_bot:
        return

    text = (message.text or "").strip()

    # Bo'sh xabar
    if not text:
        return

    # Commandlarga aralashmaydi
    if text.startswith("/"):
        return

    if client is None:
        await message.answer(
            "⚠️ EDU AI hozircha sozlanmagan."
        )
        return

    try:
        response = await client.responses.create(
            model="gpt-5-mini",
            instructions=SYSTEM_PROMPT,
            input=text,
        )

        answer = response.output_text.strip()

        if not answer:
            await message.answer(
                "⚠️ Javob olishda muammo yuz berdi."
            )
            return

        # Telegram xabar uzunligi chegarasini hisobga olamiz
        max_length = 4000

        if len(answer) <= max_length:
            await message.answer(
                f"🤖 <b>EDU AI:</b>\n\n{answer}",
                parse_mode="HTML"
            )
        else:
            for i in range(0, len(answer), max_length):
                await message.answer(
                    f"🤖 <b>EDU AI:</b>\n\n"
                    f"{answer[i:i + max_length]}",
                    parse_mode="HTML"
                )

    except Exception as error:
        print("❌ EDU AI XATOSI:", repr(error))

        await message.answer(
            "⚠️ Hozir javob berishda texnik muammo yuz berdi. "
            "Birozdan keyin qayta urinib ko‘ring."
        )
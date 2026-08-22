from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import (
    add_announcement,
    get_announcements,
    get_group_id,
)


router = Router()


# ============================================================
# FSM
# ============================================================

class AnnouncementStates(StatesGroup):
    waiting_title = State()
    waiting_text = State()


# ============================================================
# ADMIN TEKSHIRISH
# ============================================================

def is_admin(message: Message) -> bool:
    return (
        message.from_user is not None
        and message.from_user.id == ADMIN_ID
    )


def is_admin_callback(
    callback: CallbackQuery
) -> bool:

    return (
        callback.from_user is not None
        and callback.from_user.id == ADMIN_ID
    )


# ============================================================
# 📢 E'LONLAR MENYUSI
# ============================================================

@router.message(F.text == "📢 E'lonlar")
async def announcements_button(
    message: Message
):

    if not is_admin(message):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Yangi e'lon",
                    callback_data="announcement_new"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 E'lonlar tarixi",
                    callback_data="announcement_history"
                )
            ],
        ]
    )

    await message.answer(
        "📢 <b>E'LONLAR</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ============================================================
# ➕ YANGI E'LON
# ============================================================

@router.callback_query(
    F.data == "announcement_new"
)
async def announcement_new(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):
        return

    await state.clear()

    await state.set_state(
        AnnouncementStates.waiting_title
    )

    await callback.message.answer(
        "📢 <b>YANGI E'LON</b>\n\n"
        "E'lon sarlavhasini yozing.\n\n"
        "Masalan:\n"
        "📚 Ertangi dars haqida",
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 📝 SARLAVHA
# ============================================================

@router.message(
    AnnouncementStates.waiting_title
)
async def announcement_title(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    if not message.text:
        await message.answer(
            "❌ Sarlavha matn ko‘rinishida bo‘lishi kerak."
        )
        return

    title = message.text.strip()

    if len(title) < 2:
        await message.answer(
            "❌ Sarlavha juda qisqa."
        )
        return

    await state.update_data(
        title=title
    )

    await state.set_state(
        AnnouncementStates.waiting_text
    )

    await message.answer(
        "📝 <b>2-BOSQICH</b>\n\n"
        "Endi e'lon matnini yuboring.",
        parse_mode="HTML"
    )


# ============================================================
# 📝 E'LON MATNI
# ============================================================

@router.message(
    AnnouncementStates.waiting_text
)
async def announcement_text(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    if not message.text:
        await message.answer(
            "❌ E'lon matn ko‘rinishida bo‘lishi kerak."
        )
        return

    text = message.text.strip()

    if len(text) < 2:
        await message.answer(
            "❌ E'lon matni juda qisqa."
        )
        return

    data = await state.get_data()

    title = data.get(
        "title",
        "E'lon"
    )

    await state.update_data(
        text=text
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Guruhga yuborish",
                    callback_data="announcement_send"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="announcement_cancel"
                )
            ],
        ]
    )

    await message.answer(
        "👀 <b>E'LONNI TEKSHIRISH</b>\n\n"
        f"📢 <b>{title}</b>\n\n"
        f"{text}\n\n"
        "Yuborishga tayyormi?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ============================================================
# ✅ GURUHGA YUBORISH
# ============================================================

@router.callback_query(
    F.data == "announcement_send"
)
async def announcement_send(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):
        return

    data = await state.get_data()

    title = data.get("title")
    text = data.get("text")

    if not title or not text:

        await callback.answer(
            "❌ E'lon ma'lumotlari topilmadi.",
            show_alert=True
        )

        await state.clear()
        return

    group_id = get_group_id()

    if not group_id:

        await callback.message.answer(
            "❌ Guruh hali bog‘lanmagan.\n\n"
            "Avval guruhga botni qo‘shing va:\n\n"
            "/setgroup\n\n"
            "komandasini yuboring."
        )

        await callback.answer()
        return

    announcement_message = (
        "📢 <b>E'LON</b>\n\n"
        f"🔔 <b>{title}</b>\n\n"
        f"{text}\n\n"
        "🏫 9-E sinf"
    )

    try:

        await callback.bot.send_message(
            chat_id=int(group_id),
            text=announcement_message,
            parse_mode="HTML"
        )

        add_announcement(
            title=title,
            text=text,
            created_by=callback.from_user.id,
            is_pinned=0
        )

        await callback.message.edit_text(
            "✅ <b>E'LON YUBORILDI!</b>\n\n"
            f"📢 {title}\n\n"
            f"{text}",
            parse_mode="HTML"
        )

        await state.clear()

        await callback.answer(
            "Yuborildi ✅"
        )

    except Exception as error:

        print(
            "❌ E'LON XATOSI:",
            repr(error)
        )

        await callback.message.answer(
            "❌ E'lonni yuborishda xatolik yuz berdi.\n\n"
            f"<code>{error}</code>",
            parse_mode="HTML"
        )

        await callback.answer()


# ============================================================
# ❌ BEKOR QILISH
# ============================================================

@router.callback_query(
    F.data == "announcement_cancel"
)
async def announcement_cancel(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):
        return

    await state.clear()

    await callback.message.edit_text(
        "❌ <b>E'lon bekor qilindi.</b>",
        parse_mode="HTML"
    )

    await callback.answer(
        "Bekor qilindi."
    )


# ============================================================
# 📋 E'LONLAR TARIXI
# ============================================================

@router.callback_query(
    F.data == "announcement_history"
)
async def announcement_history(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    announcements = get_announcements()

    if not announcements:

        await callback.message.edit_text(
            "📭 <b>E'lonlar tarixi bo‘sh.</b>",
            parse_mode="HTML"
        )

        await callback.answer()
        return

    text = (
        "📋 <b>E'LONLAR TARIXI</b>\n\n"
    )

    for index, announcement in enumerate(
        announcements[:20],
        start=1
    ):

        title = announcement["title"]
        announcement_text = announcement["text"]
        created_at = announcement["created_at"]

        text += (
            f"{index}. 📢 <b>{title}</b>\n"
            f"{announcement_text}\n"
            f"🕐 {created_at}\n\n"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="announcement_back"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ⬅️ ORQAGA
# ============================================================

@router.callback_query(
    F.data == "announcement_back"
)
async def announcement_back(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Yangi e'lon",
                    callback_data="announcement_new"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 E'lonlar tarixi",
                    callback_data="announcement_history"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        "📢 <b>E'LONLAR</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()
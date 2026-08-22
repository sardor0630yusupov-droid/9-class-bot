import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_ID

from handlers.admin import router as admin_router

from database import (
    init_database,
    get_student_by_telegram_id,
    link_student_by_code,
)

from keyboards.admin import admin_keyboard
from scheduler import scheduler_loop


dp = Dispatcher()

dp.include_router(admin_router)


def student_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Davomat",
                    callback_data="student_attendance"
                ),
                InlineKeyboardButton(
                    text="⭐ Baholar",
                    callback_data="student_grades"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Uy vazifalari",
                    callback_data="student_homework"
                ),
                InlineKeyboardButton(
                    text="📅 Dars jadvali",
                    callback_data="student_schedule"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 E'lonlar",
                    callback_data="student_announcements"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Mening statistikam",
                    callback_data="student_statistics"
                )
            ]
        ]
    )


@dp.message(Command("id"))
async def id_handler(message: Message):

    await message.answer(
        "🆔 Sizning Telegram ID'ingiz:\n\n"
        f"<code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )


@dp.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id

    if user_id == ADMIN_ID:

        await message.answer(
            "👋 Assalomu alaykum, Sardor!\n\n"
            "🏫 <b>9-E SCHOOL BOT</b>\n"
            "⚙️ <b>ADMIN PANEL</b>\n\n"
            "Kerakli bo‘limni tanlang:",
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )
        return

    parts = (message.text or "").strip().split(maxsplit=1)

    if len(parts) == 2:

        code = parts[1].strip()

        if code.isdigit() and len(code) == 6:

            student = link_student_by_code(
                user_id,
                code
            )

            if student:

                await message.answer(
                    "✅ <b>O‘QUVCHI PROFILI ULANDI!</b>\n\n"
                    f"👤 F.I.SH: <b>{student['full_name']}</b>\n"
                    f"🏫 Sinf: <b>{student['class_name']}</b>\n\n"
                    "Endi botdan o‘quvchi sifatida foydalanishingiz mumkin.",
                    reply_markup=student_keyboard(),
                    parse_mode="HTML"
                )
                return

            await message.answer(
                "❌ <b>Kod noto‘g‘ri yoki muddati tugagan.</b>\n\n"
                "Adminingizdan yangi o‘quvchi kodini so‘rang.",
                parse_mode="HTML"
            )
            return

    student = get_student_by_telegram_id(user_id)

    if student:

        await message.answer(
            "👨‍🎓 <b>O‘QUVCHI PANELI</b>\n\n"
            f"👤 F.I.SH: <b>{student['full_name']}</b>\n"
            f"🏫 Sinf: <b>{student['class_name']}</b>\n\n"
            "Kerakli bo‘limni tanlang:",
            reply_markup=student_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        "👋 <b>9-E SCHOOL BOT</b>\n\n"
        "❌ Siz hali o‘quvchi sifatida ulanmagansiz.\n\n"
        "👨‍🎓 O‘quvchi bo‘lsangiz, admin bergan kodni:\n"
        "<code>/student 123456</code>\n\n"
        "yoki:\n"
        "<code>/start 123456</code>"
        ,
        parse_mode="HTML"
    )


@dp.message(Command("student"))
async def student_command(message: Message):

    parts = (message.text or "").strip().split()

    if len(parts) != 2:

        await message.answer(
            "👨‍🎓 <b>O‘QUVCHI ULANISHI</b>\n\n"
            "Admin bergan 6 xonali kodni yuboring:\n\n"
            "<code>/student 123456</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].strip()

    if not code.isdigit() or len(code) != 6:

        await message.answer(
            "❌ Kod 6 xonali raqam bo‘lishi kerak.",
            parse_mode="HTML"
        )
        return

    try:

        student = link_student_by_code(
            message.from_user.id,
            code
        )

    except Exception as error:

        print(
            "❌ STUDENT LINK XATOSI:",
            repr(error)
        )

        await message.answer(
            "❌ Ulanishda server xatosi yuz berdi.",
            parse_mode="HTML"
        )
        return

    if not student:

        await message.answer(
            "❌ <b>Kod noto‘g‘ri yoki muddati tugagan.</b>\n\n"
            "Adminingizdan yangi kod so‘rang.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "✅ <b>MUVAFFAQIYATLI ULANDI!</b>\n\n"
        f"👤 F.I.SH: <b>{student['full_name']}</b>\n"
        f"🏫 Sinf: <b>{student['class_name']}</b>\n\n"
        "👨‍🎓 O‘quvchi profilingiz tayyor.",
        reply_markup=student_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "student_statistics")
async def student_statistics(callback: CallbackQuery):

    from database import (
        get_student_attendance,
        get_student_grades,
        get_homework
    )

    student = get_student_by_telegram_id(
        callback.from_user.id
    )

    if not student:

        await callback.answer(
            "❌ O‘quvchi profilingiz topilmadi.",
            show_alert=True
        )
        return

    attendance = get_student_attendance(student["id"])

    present = 0
    absent = 0
    warning = 0

    for item in attendance:

        status = str(item["status"]).lower()

        if status == "present":
            present += 1

        elif status == "absent":
            absent += 1

        elif status == "warning":
            warning += 1

    total_attendance = present + absent + warning

    attendance_percent = (
        round(present / total_attendance * 100, 1)
        if total_attendance else 0
    )

    grades = get_student_grades(student["id"])

    grade_sum = 0
    grade_count = 0

    for item in grades:

        try:
            grade_sum += float(item["grade"])
            grade_count += 1
        except (TypeError, ValueError):
            pass

    average_grade = (
        round(grade_sum / grade_count, 2)
        if grade_count else "—"
    )

    homework = get_homework()

    text = (
        "📊 <b>MENING STATISTIKAM</b>\n\n"
        f"👤 O‘quvchi: <b>{student['full_name']}</b>\n"
        f"🏫 Sinf: <b>{student['class_name']}</b>\n\n"

        "📊 <b>DAVOMAT</b>\n"
        f"├─ Jami: <b>{total_attendance}</b>\n"
        f"├─ ✅ Keldi: <b>{present}</b>\n"
        f"├─ ❌ Kelmadi: <b>{absent}</b>\n"
        f"├─ ⚠️ Sababli: <b>{warning}</b>\n"
        f"└─ 📈 Foiz: <b>{attendance_percent}%</b>\n\n"

        "⭐ <b>BAHOLARI</b>\n"
        f"├─ Jami baho: <b>{grade_count}</b>\n"
        f"└─ 📈 O‘rtacha: <b>{average_grade}</b>\n\n"

        "📝 <b>UY VAZIFALARI</b>\n"
        f"└─ Jami: <b>{len(homework)}</b>"
    )

    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Bosh sahifa",
                    callback_data="student_home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "student_home")
async def student_home_callback(callback: CallbackQuery):

    student = get_student_by_telegram_id(
        callback.from_user.id
    )

    if not student:

        await callback.answer(
            "❌ O‘quvchi profilingiz topilmadi.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "👨‍🎓 <b>O‘QUVCHI PANELI</b>\n\n"
        f"👤 F.I.SH: <b>{student['full_name']}</b>\n"
        f"🏫 Sinf: <b>{student['class_name']}</b>\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=student_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


async def main():

    print()
    print("========================================")
    print("       9-E SCHOOL BOT")
    print("========================================")
    print()

    print("🗄 Database tekshirilmoqda...")

    init_database()

    print("✅ Database tayyor!")

    bot = Bot(token=BOT_TOKEN)

    print("🤖 Bot yaratildi!")

    scheduler_task = asyncio.create_task(
        scheduler_loop(bot)
    )

    print("⏰ Scheduler ishga tushdi!")
    print("🚀 BOT ISHLASHGA TAYYOR!")
    print("========================================")

    try:

        await dp.start_polling(bot)

    except KeyboardInterrupt:

        print("\n🛑 Bot to‘xtatildi.")

    except Exception as error:

        print("\n❌ BOT XATOSI:")
        print(repr(error))

    finally:

        if not scheduler_task.done():

            scheduler_task.cancel()

            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass

        await bot.session.close()

        print("🔴 Bot yopildi.")


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:

        print("\n👋 Dastur to‘xtatildi.")

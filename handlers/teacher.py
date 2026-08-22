from datetime import datetime

from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command

from database import (
    get_teacher_by_telegram_id,
    get_students,
    get_student,
    add_attendance,
    get_student_attendance,
    get_schedule,
    get_attendance_by_date
)


router = Router()


# ==================================================
# O'QITUVCHINI TEKSHIRISH
# ==================================================

def is_teacher(user_id):

    return (
        get_teacher_by_telegram_id(user_id)
        is not None
    )


# ==================================================
# /teacher
# ==================================================

@router.message(Command("teacher"))
async def teacher_command(message: Message):

    if not is_teacher(message.from_user.id):

        await message.answer(
            "⛔ Siz o‘qituvchi sifatida "
            "ro‘yxatdan o‘tkazilmagansiz."
        )

        return

    await show_teacher_panel(message)


# ==================================================
# O'QITUVCHI PANELI
# ==================================================

async def show_teacher_panel(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Davomat olish",
                    callback_data="teacher_attendance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Bugungi davomat",
                    callback_data="attendance_today"
                )
            ]
        ]
    )

    await message.answer(
        "👨‍🏫 **O‘QITUVCHI PANELI**\n\n"
        "🏫 9-E School Bot\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ==================================================
# DAVOMAT OLISH — DARS TANLASH
# ==================================================

@router.callback_query(
    F.data == "teacher_attendance"
)
async def teacher_attendance(
    callback: CallbackQuery
):

    if not is_teacher(callback.from_user.id):

        await callback.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    # Python:
    # Monday = 0
    # Sunday = 6
    #
    # Bizning database:
    # Dushanba = 1
    # Shanba = 6

    today_python = datetime.now().weekday()

    if today_python == 6:

        await callback.message.answer(
            "🌙 Bugun yakshanba.\n\n"
            "🏫 Bugun dars yo‘q."
        )

        await callback.answer()

        return

    today = today_python + 1

    schedules = get_schedule(today)

    if not schedules:

        await callback.message.answer(
            "📚 Bugun uchun dars jadvali "
            "kiritilmagan."
        )

        await callback.answer()

        return

    day_names = {
        1: "Dushanba",
        2: "Seshanba",
        3: "Chorshanba",
        4: "Payshanba",
        5: "Juma",
        6: "Shanba"
    }

    buttons = []

    for lesson in schedules:

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"{lesson['lesson_number']}️⃣ "
                    f"{lesson['subject']} "
                    f"⏰ {lesson['start_time']}"
                ),
                callback_data=(
                    f"take_attendance_"
                    f"{lesson['id']}"
                )
            )
        ])

    await callback.message.answer(
        "📊 **BUGUNGI DAVOMAT**\n\n"
        f"📅 {day_names[today]}\n"
        f"📆 {datetime.now().strftime('%d.%m.%Y')}\n\n"
        "Davomat olinadigan darsni tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="Markdown"
    )

    await callback.answer()


# ==================================================
# O'QUVCHILARNI KO'RSATISH
# ==================================================

@router.callback_query(
    F.data.startswith("take_attendance_")
)
async def take_attendance(
    callback: CallbackQuery
):

    if not is_teacher(callback.from_user.id):
        return

    schedule_id = int(
        callback.data.split("_")[-1]
    )

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # Bugungi kun
    today_day = datetime.now().weekday() + 1

    schedules = get_schedule(today_day)

    selected_schedule = None

    for schedule in schedules:

        if schedule["id"] == schedule_id:

            selected_schedule = schedule
            break

    if selected_schedule is None:

        await callback.answer(
            "❌ Dars topilmadi.",
            show_alert=True
        )

        return

    students = get_students()

    if not students:

        await callback.message.answer(
            "❌ O‘quvchilar bazasi bo‘sh."
        )

        await callback.answer()

        return

    buttons = []

    for student in students:

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {student['full_name']}",
                callback_data=(
                    f"mark_student_"
                    f"{student['id']}_"
                    f"{schedule_id}"
                )
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="📊 Yakunlash",
            callback_data=(
                f"attendance_finish_"
                f"{schedule_id}"
            )
        )
    ])

    await callback.message.answer(
        "📝 **DAVOMAT OLISH**\n\n"
        f"📚 Fan: {selected_schedule['subject']}\n"
        f"⏰ {selected_schedule['start_time']}"
        f"–{selected_schedule['end_time']}\n"
        f"📅 {today}\n\n"
        "O‘quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="Markdown"
    )

    await callback.answer()


# ==================================================
# O'QUVCHINING HOLATINI TANLASH
# ==================================================

@router.callback_query(
    F.data.startswith("mark_student_")
)
async def mark_student(
    callback: CallbackQuery
):

    if not is_teacher(callback.from_user.id):
        return

    parts = callback.data.split("_")

    student_id = int(parts[2])
    schedule_id = int(parts[3])

    student = get_student(student_id)

    if student is None:

        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )

        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Keldi",
                    callback_data=(
                        f"save_att_"
                        f"{student_id}_"
                        f"{schedule_id}_present"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Kelmadi",
                    callback_data=(
                        f"save_att_"
                        f"{student_id}_"
                        f"{schedule_id}_absent"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚠️ Kirdi, qatnashmadi",
                    callback_data=(
                        f"save_att_"
                        f"{student_id}_"
                        f"{schedule_id}_warning"
                    )
                )
            ]
        ]
    )

    await callback.message.answer(
        f"👤 **{student['full_name']}**\n\n"
        "Davomat holatini tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    await callback.answer()


# ==================================================
# DAVOMATNI SAQLASH
# ==================================================

@router.callback_query(
    F.data.startswith("save_att_")
)
async def save_attendance(
    callback: CallbackQuery
):

    if not is_teacher(callback.from_user.id):
        return

    parts = callback.data.split("_")

    student_id = int(parts[2])
    schedule_id = int(parts[3])
    status = parts[4]

    teacher = get_teacher_by_telegram_id(
        callback.from_user.id
    )

    if teacher is None:

        await callback.answer(
            "⛔ O‘qituvchi topilmadi.",
            show_alert=True
        )

        return

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    today_day = datetime.now().weekday() + 1

    schedules = get_schedule(today_day)

    selected_schedule = None

    for schedule in schedules:

        if schedule["id"] == schedule_id:

            selected_schedule = schedule
            break

    if selected_schedule is None:

        await callback.answer(
            "❌ Dars topilmadi.",
            show_alert=True
        )

        return

    add_attendance(
        student_id=student_id,
        attendance_date=today,
        status=status,
        lesson_number=selected_schedule[
            "lesson_number"
        ],
        teacher_id=teacher["id"]
    )

    status_names = {
        "present": "✅ Keldi",
        "absent": "❌ Kelmadi",
        "warning": "⚠️ Kirdi, qatnashmadi"
    }

    await callback.message.edit_text(
        "✅ **DAVOMAT SAQLANDI**\n\n"
        f"👤 {get_student(student_id)['full_name']}\n"
        f"📚 {selected_schedule['subject']}\n"
        f"📅 {today}\n"
        f"📌 {status_names[status]}",
        parse_mode="Markdown"
    )

    await callback.answer(
        "Saqlandi ✅"
    )


# ==================================================
# YAKUNIY STATISTIKA
# ==================================================

@router.callback_query(
    F.data.startswith("attendance_finish_")
)
async def attendance_finish(
    callback: CallbackQuery
):

    if not is_teacher(callback.from_user.id):
        return

    schedule_id = int(
        callback.data.split("_")[-1]
    )

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    today_day = datetime.now().weekday() + 1

    schedules = get_schedule(today_day)

    selected_schedule = None

    for schedule in schedules:

        if schedule["id"] == schedule_id:

            selected_schedule = schedule
            break

    if selected_schedule is None:

        await callback.answer(
            "❌ Dars topilmadi.",
            show_alert=True
        )

        return

    students = get_students()

    present = 0
    absent = 0
    warning = 0
    not_marked = 0

    for student in students:

        records = get_student_attendance(
            student["id"]
        )

        found = False

        for record in records:

            if (
                record["attendance_date"]
                == today
                and
                record["lesson_number"]
                ==
                selected_schedule[
                    "lesson_number"
                ]
            ):

                found = True

                if record["status"] == "present":
                    present += 1

                elif record["status"] == "absent":
                    absent += 1

                elif record["status"] == "warning":
                    warning += 1

                break

        if not found:
            not_marked += 1

    total = len(students)

    await callback.message.answer(
        "📊 **DAVOMAT YAKUNI**\n\n"
        f"📚 Fan: {selected_schedule['subject']}\n"
        f"📅 Sana: {today}\n\n"
        f"👥 Jami o‘quvchi: {total}\n"
        f"✅ Keldi: {present}\n"
        f"❌ Kelmadi: {absent}\n"
        f"⚠️ Qatnashmadi: {warning}\n"
        f"⏳ Belgilanmagan: {not_marked}",
        parse_mode="Markdown"
    )

    await callback.answer()


# ==================================================
# BUGUNGI UMUMIY DAVOMAT
# ==================================================

@router.callback_query(
    F.data == "attendance_today"
)
async def attendance_today(
    callback: CallbackQuery
):

    if not is_teacher(callback.from_user.id):
        return

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    records = get_attendance_by_date(
        today
    )

    if not records:

        await callback.message.answer(
            "📭 Bugun hali davomat olinmagan."
        )

        await callback.answer()

        return

    present = 0
    absent = 0
    warning = 0

    for record in records:

        if record["status"] == "present":
            present += 1

        elif record["status"] == "absent":
            absent += 1

        elif record["status"] == "warning":
            warning += 1

    await callback.message.answer(
        "📊 **BUGUNGI DAVOMAT**\n\n"
        f"📅 {today}\n\n"
        f"✅ Keldi: {present}\n"
        f"❌ Kelmadi: {absent}\n"
        f"⚠️ Qatnashmadi: {warning}\n\n"
        f"📝 Jami belgilangan: "
        f"{len(records)} ta",
        parse_mode="Markdown"
    )

    await callback.answer()


# ==================================================
# O'QITUVCHI UCHUN QULAY COMMAND
# ==================================================

@router.message(Command("myattendance"))
async def myattendance_command(
    message: Message
):

    if not is_teacher(message.from_user.id):

        await message.answer(
            "⛔ Siz o‘qituvchi emassiz."
        )

        return

    await show_teacher_panel(message)
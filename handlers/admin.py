from datetime import datetime
import os
from html import escape

from aiogram import Router, F

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.filters import Command

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
class HomeworkStates(StatesGroup):
    subject = State()
    homework_text = State()
    due_date = State()


from config import ADMIN_ID

from database import (
    # ========================================================
    # 👥 O'QUVCHILAR
    # ========================================================

    add_student,
    get_students,
    get_student,
    search_students,
    update_student_birth_date,

    # ========================================================
    # 👨‍🏫 O'QITUVCHILAR
    # ========================================================

    add_teacher,
    get_teachers,
    delete_teacher,

    # ========================================================
    # 📅 DARS JADVALI
    # ========================================================

    get_schedule,
    get_all_schedules,
    add_schedule,
    delete_schedule,

    # ========================================================
    # 🎉 BAYRAMLAR
    # ========================================================

    add_holiday,
    get_holidays,
    delete_holiday,

    # ========================================================
    # 📊 DAVOMAT
    # ========================================================

    add_attendance,
    get_attendance_by_date,
    get_student_attendance,

    # ========================================================
    # ⭐ BAHOLAR
    # ========================================================

    add_grade,
    get_student_grades,

    # ========================================================
    # 📝 UY VAZIFALARI
    # ========================================================

    get_homework,
    add_homework,
    delete_homework,

    # ========================================================
    # 📢 E'LONLAR
    # ========================================================

    add_announcement,
    get_announcements,
    delete_announcement,

    # ========================================================
    # 📸 TADBIRLAR
    # ========================================================

    get_events,
    create_student_code
)

from utils.excel import (
    read_students_excel
)

from scheduler import (
    save_group_id,
    get_group_id
)


# ============================================================
# 🤖 ADMIN ROUTER
# ============================================================

router = Router()


# ============================================================
# ADMIN TEKSHIRISH
# ============================================================

def is_admin(message: Message) -> bool:
    return (
        message.from_user is not None
        and message.from_user.id == ADMIN_ID
    )


def is_admin_callback(callback: CallbackQuery) -> bool:
    return (
        callback.from_user is not None
        and callback.from_user.id == ADMIN_ID
    )


# ============================================================
# FSM
# ============================================================

class AdminStates(StatesGroup):

    searching_student = State()

    adding_teacher_name = State()
    adding_teacher_id = State()
    adding_teacher_subject = State()

    adding_schedule_day = State()
    adding_schedule_lesson = State()
    adding_schedule_subject = State()
    adding_schedule_start = State()
    adding_schedule_end = State()

    adding_holiday_name = State()
    adding_holiday_date = State()
    adding_holiday_day_off = State()

    # E'lon
    announcement_title = State()
    announcement_text = State()


# ============================================================
# /admin
# ============================================================

@router.message(Command("admin"))
async def admin_command(message: Message):

    if not is_admin(message):
        await message.answer(
            "⛔ Sizda admin huquqi yo‘q."
        )
        return

    await message.answer(
        "⚙️ ADMIN PANEL\n\n"
        "🏫 9-E School Bot\n\n"
        "Kerakli bo‘limni tanlang:"
    )


# ============================================================
# O'QUVCHILAR
# ============================================================

@router.message(F.text == "👥 O‘quvchilar")
async def students_button(message: Message):

    if not is_admin(message):
        return

    students = get_students()

    if not students:

        await message.answer(
            "👥 9-E O‘QUVCHILARI\n\n"
            "❌ Hozircha o‘quvchilar bazasi bo‘sh."
        )

        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 O‘quvchilar ro‘yxati",
                    callback_data="students_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 O‘quvchini qidirish",
                    callback_data="student_search"
                )
            ]
        ]
    )

    await message.answer(
        "👥 9-E O‘QUVCHILARI\n\n"
        f"📊 Jami: {len(students)} nafar\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=keyboard
    )


# ============================================================
# O'QUVCHILAR RO'YXATI
# ============================================================

@router.callback_query(
    F.data == "students_list"
)
async def students_list(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
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
    callback_data=f"profile_{student['id']}"
)
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="students_back"
        )
    ])

    await callback.message.edit_text(
        "👥 **9-E O‘QUVCHILARI**\n\n"
        f"📊 Jami: {len(students)} ta\n\n"
        "Profilini ko‘rish uchun o‘quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="Markdown"
    )

    await callback.answer()

    

# ============================================================
# 👤 O'QUVCHI PROFILI
# ============================================================

# ============================================================
# 👤 O'QUVCHI PROFILI
# ============================================================

@router.callback_query(
    F.data.regexp(r"^profile_\d+$")
)
async def student_profile(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        await callback.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )
        return

    try:
        student_id = int(
            callback.data.split("_")[-1]
        )
    except (ValueError, TypeError):

        await callback.answer(
            "❌ O‘quvchi ID xato.",
            show_alert=True
        )
        return

    student = get_student(
        student_id
    )

    if not student:

        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    birth_date = (
        student["birth_date"]
        if student["birth_date"]
        else "Kiritilmagan"
    )

    # --------------------------------------------------------
    # DAVOMAT
    # --------------------------------------------------------

    try:
        attendance = get_student_attendance(
            student_id
        )
    except Exception:
        attendance = []

    present = 0
    absent = 0
    warning = 0

    for record in attendance:

        status = record["status"]

        if status == "present":
            present += 1

        elif status == "absent":
            absent += 1

        elif status == "warning":
            warning += 1

    total_attendance = (
        present
        + absent
        + warning
    )

    if total_attendance > 0:

        attendance_percent = round(
            present / total_attendance * 100,
            1
        )

    else:

        attendance_percent = 0

    # --------------------------------------------------------
    # PROFIL
    # --------------------------------------------------------

    text = (
        "👨‍🎓 <b>O‘QUVCHI PROFILI</b>\n\n"

        f"👤 <b>F.I.SH:</b> "
        f"{student['full_name']}\n"

        f"🏫 <b>Sinf:</b> "
        f"{student['class_name']}\n"

        f"🎂 <b>Tug‘ilgan sana:</b> "
        f"{birth_date}\n\n"

        "📊 <b>DAVOMAT</b>\n\n"

        f"✅ Keldi: {present}\n"
        f"❌ Kelmadi: {absent}\n"
        f"⚠️ Sababli: {warning}\n"
        f"📈 Davomat: {attendance_percent}%"
    )

    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⭐ Baholar",
                callback_data=f"profile_grades_{student_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Davomat",
                callback_data=f"profile_att_{student_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔐 O‘quvchiga kod yaratish",
                callback_data=f"student_code_{student_id}"
            )
        ],
    ]
)
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 🔐 O'QUVCHIGA ULANISH KODI YARATISH
# ============================================================

@router.callback_query(
    F.data.startswith("student_code_")
)
async def student_code_button(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        await callback.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )
        return

    try:
        student_id = int(
            callback.data.split("_")[-1]
        )
    except (ValueError, TypeError):
        await callback.answer(
            "❌ O‘quvchi ID xato.",
            show_alert=True
        )
        return

    student = get_student(student_id)

    if not student:
        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    try:
        code = create_student_code(student_id)
    except Exception as error:
        print(
            "❌ STUDENT CODE XATOSI:",
            repr(error)
        )
        await callback.answer(
            "❌ Kod yaratishda xatolik.",
            show_alert=True
        )
        return

    await callback.message.answer(
        "🔐 <b>O‘QUVCHI ULANISH KODI</b>\n\n"
        f"👤 O‘quvchi: <b>{escape(str(student['full_name']))}</b>\n"
        f"🏫 Sinf: <b>{escape(str(student['class_name']))}</b>\n\n"
        f"🔑 KOD: <code>{code}</code>\n\n"
        "📱 O‘quvchi botga quyidagicha yuboradi:\n"
        f"<code>/student {code}</code>\n\n"
        "⏰ Kod 24 soat amal qiladi.\n"
        "✅ Kod ishlatilganda o‘quvchining Telegram ID'si "
        "bazaga avtomatik ulanadi.",
        parse_mode="HTML"
    )

    await callback.answer(
        "🔐 O‘quvchi kodi yaratildi!"
    )


# ============================================================
# 📊 O‘QUVCHI DAVOMATI
# ============================================================

@router.callback_query(
    F.data.startswith("profile_att_")
)
async def student_attendance_profile(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    try:
        student_id = int(
            callback.data.split("_")[-1]
        )
    except ValueError:
        await callback.answer(
            "❌ O‘quvchi ID xato.",
            show_alert=True
        )
        return

    student = get_student(student_id)

    if not student:
        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    try:
        records = get_student_attendance(
            student_id
        )
    except Exception as error:

        print(
            "❌ Davomat xatosi:",
            repr(error)
        )

        await callback.message.answer(
            f"❌ Davomatni olishda xatolik:\n{error}"
        )

        await callback.answer()
        return

    present = 0
    absent = 0
    warning = 0

    for record in records:

        status = record["status"]

        if status == "present":
            present += 1

        elif status == "absent":
            absent += 1

        elif status == "warning":
            warning += 1

    total = (
        present
        + absent
        + warning
    )

    if total > 0:
        percentage = round(
            present / total * 100,
            1
        )
    else:
        percentage = 0

    text = (
        "📊 <b>O‘QUVCHI DAVOMATI</b>\n\n"
        f"👤 <b>{student['full_name']}</b>\n"
        f"🏫 Sinf: <b>{student['class_name']}</b>\n\n"

        f"✅ Keldi: <b>{present}</b>\n"
        f"❌ Kelmadi: <b>{absent}</b>\n"
        f"⚠️ Sababli: <b>{warning}</b>\n"
        f"📚 Jami: <b>{total}</b>\n\n"

        f"📈 Davomat: <b>{percentage}%</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Davomat tarixi",
                    callback_data=f"profile_att_history_{student_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Profil",
                    callback_data=f"profile_{student_id}"
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
# ===========================================================
# ⭐ O'QUVCHI BAHOLARI
# ============================================================

@router.callback_query(
    F.data.startswith("profile_grades_")
)
async def student_profile_grades(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        await callback.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )
        return

    try:
        student_id = int(
            callback.data.split("_")[-1]
        )
    except (ValueError, TypeError):

        await callback.answer(
            "❌ O‘quvchi ID xato.",
            show_alert=True
        )
        return

    student = get_student(student_id)

    if not student:

        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    try:
        grades = get_student_grades(
            student_id
        )

    except Exception as error:

        print(
            "❌ Baholarni olish xatosi:",
            repr(error)
        )

        await callback.answer(
            "❌ Baholarni olishda xatolik.",
            show_alert=True
        )
        return

    # --------------------------------------------------------
    # ORQAGA TUGMASI
    # --------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Profilga qaytish",
                    callback_data=f"profile_{student_id}"
                )
            ]
        ]
    )

    # --------------------------------------------------------
    # BAHO YO'Q
    # --------------------------------------------------------

    if not grades:

        await callback.message.edit_text(
            "⭐ <b>O‘QUVCHI BAHOLARI</b>\n\n"
            f"👤 <b>{escape(str(student['full_name']))}</b>\n"
            f"🏫 Sinf: <b>{escape(str(student['class_name']))}</b>\n\n"
            "📭 Hozircha baholar kiritilmagan.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await callback.answer()
        return

    # --------------------------------------------------------
    # FANLAR BO'YICHA GURUHLASH
    # --------------------------------------------------------

    subjects = {}

    total_sum = 0
    total_count = 0

    for grade in grades:

        try:

            if hasattr(
                grade,
                "keys"
            ):

                subject = grade["subject"]
                value = grade["grade"]

            else:

                subject = (
                    grade[1]
                    if len(grade) > 1
                    else "Noma’lum fan"
                )

                value = (
                    grade[2]
                    if len(grade) > 2
                    else 0
                )

        except Exception:

            continue

        subject = str(
            subject
        ).strip()

        try:
            value = int(value)

        except (TypeError, ValueError):
            continue

        if subject not in subjects:

            subjects[subject] = []

        subjects[subject].append(
            value
        )

        total_sum += value
        total_count += 1

    # --------------------------------------------------------
    # MATN
    # --------------------------------------------------------

    text = (
        "⭐ <b>O‘QUVCHI BAHOLARI</b>\n\n"
        f"👤 <b>{escape(str(student['full_name']))}</b>\n"
        f"🏫 Sinf: <b>{escape(str(student['class_name']))}</b>\n\n"
    )

    for subject, values in subjects.items():

        subject_sum = sum(
            values
        )

        subject_count = len(
            values
        )

        subject_average = round(
            subject_sum / subject_count,
            2
        )

        text += (
            f"📚 <b>{escape(subject)}</b>\n"
            f"   ⭐ O‘rtacha: <b>{subject_average}</b>\n"
            f"   📝 Baholar: <b>"
            f"{', '.join(map(str, values))}</b>\n"
            f"   📊 Jami: <b>{subject_count} ta</b>\n\n"
        )

    # --------------------------------------------------------
    # UMUMIY
    # --------------------------------------------------------

    if total_count:

        overall_average = round(
            total_sum / total_count,
            2
        )

        text += (
            "━━━━━━━━━━━━━━\n"
            f"📊 <b>UMUMIY O‘RTACHA: "
            f"{overall_average}</b>\n"
            f"📝 <b>Jami baholar: "
            f"{total_count} ta</b>"
        )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

# ============================================================
# O'QUVCHI QIDIRISH BOSHLASH
# ============================================================

@router.callback_query(
    F.data == "student_search"
)
async def student_search_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):
        return

    await state.set_state(
        AdminStates.searching_student
    )

    await callback.message.answer(
        "🔎 O‘quvchini qidirish\n\n"
        "O‘quvchining F.I.SH qismini yoki "
        "to‘liq ism-familiyasini yozing:"
    )

    await callback.answer()


# ============================================================
# O'QUVCHI QIDIRISH
# ============================================================

@router.message(
    AdminStates.searching_student
)
async def search_student_message(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    text = message.text

    if not text:
        await message.answer(
            "❌ Matn yuboring."
        )
        return

    students = search_students(
        text.strip()
    )

    if not students:

        await message.answer(
            "❌ Bunday o‘quvchi topilmadi."
        )

        await state.clear()
        return

    result = "🔎 QIDIRUV NATIJASI\n\n"

    for index, student in enumerate(
        students,
        start=1
    ):

        birth_date = (
            student["birth_date"]
            if student["birth_date"]
            else "Kiritilmagan"
        )

        result += (
            f"{index}. {student['full_name']}\n"
            f"🏫 Sinf: {student['class_name']}\n"
            f"🎂 Tug‘ilgan sana: {birth_date}\n\n"
        )

    await message.answer(
        result
    )

    await state.clear()


# ============================================================
# EXCEL QABUL QILISH
# ============================================================

@router.message(F.document)
async def excel_handler(message: Message):

    if not is_admin(message):
        return

    document = message.document

    if not document.file_name:
        await message.answer(
            "❌ Fayl nomi topilmadi."
        )
        return

    if not document.file_name.lower().endswith(".xlsx"):
        await message.answer(
            "❌ Faqat .xlsx formatdagi Excel "
            "fayl yuboring."
        )
        return

    os.makedirs(
        "data",
        exist_ok=True
    )

    await message.answer(
        "📥 Excel fayl qabul qilindi.\n"
        "⏳ O‘quvchilar ma'lumotlari tekshirilmoqda..."
    )

    try:

        file = await message.bot.get_file(
            document.file_id
        )

        file_path = os.path.join(
            "data",
            document.file_name
        )

        await message.bot.download_file(
            file.file_path,
            destination=file_path
        )

        students = read_students_excel(
            file_path
        )

        added = 0
        updated = 0
        skipped = 0

        # Bazadagi mavjud o'quvchilar
        existing_students = get_students()

        existing_names = {
            student["full_name"].strip().lower()
            for student in existing_students
        }

        for student in students:

            full_name = student.get(
                "full_name",
                ""
            ).strip()

            class_name = student.get(
                "class_name",
                "9-E"
            ).strip()

            birth_date = student.get(
                "birth_date",
                ""
            ).strip()

            if not full_name:
                skipped += 1
                continue

            # ----------------------------------------
            # MAVJUD O'QUVCHI
            # ----------------------------------------

            if full_name.lower() in existing_names:

                update_student_birth_date(
                    full_name,
                    birth_date,
                    class_name
                )

                updated += 1

            # ----------------------------------------
            # YANGI O'QUVCHI
            # ----------------------------------------

            else:

                add_student(
                    full_name,
                    class_name,
                    birth_date
                )

                added += 1

        await message.answer(
            "✅ EXCEL MUVAFFAQIYATLI QABUL QILINDI!\n\n"
            f"👥 Yangi o‘quvchilar: {added} ta\n"
            f"🔄 Yangilanganlar: {updated} ta\n"
            f"⚠️ O‘tkazib yuborilganlar: {skipped} ta\n\n"
            "🎂 Tug‘ilgan sanalar ham bazaga saqlandi."
        )

    except Exception as error:

        print(
            "EXCEL XATOSI:",
            repr(error)
        )

        await message.answer(
            "❌ Excelni o‘qishda xatolik yuz berdi.\n\n"
            f"Xato: {error}"
        )


# ============================================================
# O'QITUVCHILAR
# ============================================================

@router.message(F.text == "👨‍🏫 O‘qituvchilar")
async def teachers_button(
    message: Message
):

    if not is_admin(message):
        return

    teachers = get_teachers()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 O‘qituvchilar ro‘yxati",
                    callback_data="teachers_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ O‘qituvchi qo‘shish",
                    callback_data="teacher_add"
                )
            ]
        ]
    )

    await message.answer(
        "👨‍🏫 O‘QITUVCHILAR\n\n"
        f"📊 Jami: {len(teachers)} ta\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=keyboard
    )


# ============================================================
# O'QITUVCHILAR RO'YXATI
# ============================================================

@router.callback_query(
    F.data == "teachers_list"
)
async def teachers_list(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    teachers = get_teachers()

    if not teachers:

        await callback.message.answer(
            "👨‍🏫 Hozircha o‘qituvchilar "
            "qo‘shilmagan."
        )

        await callback.answer()
        return

    text = "👨‍🏫 O‘QITUVCHILAR\n\n"

    for index, teacher in enumerate(
        teachers,
        start=1
    ):

        subject = (
            teacher["subject"]
            if teacher["subject"]
            else "Fan kiritilmagan"
        )

        telegram_id = (
            teacher["telegram_id"]
            if teacher["telegram_id"]
            else "ID yo‘q"
        )

        text += (
            f"{index}. {teacher['full_name']}\n"
            f"📚 Fan: {subject}\n"
            f"🆔 Telegram ID: {telegram_id}\n\n"
        )

    await callback.message.answer(
        text
    )

    await callback.answer()


# ============================================================
# O'QITUVCHI QO'SHISH
# ============================================================

@router.callback_query(
    F.data == "teacher_add"
)
async def teacher_add_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):
        return

    await state.set_state(
        AdminStates.adding_teacher_name
    )

    await callback.message.answer(
        "👨‍🏫 O‘qituvchi qo‘shish\n\n"
        "1️⃣ O‘qituvchining F.I.SHini yozing:"
    )

    await callback.answer()


@router.message(
    AdminStates.adding_teacher_name
)
async def teacher_name(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.update_data(
        full_name=message.text.strip()
    )

    await state.set_state(
        AdminStates.adding_teacher_id
    )

    await message.answer(
        "🆔 O‘qituvchining Telegram ID sini yozing:"
    )


@router.message(
    AdminStates.adding_teacher_id
)
async def teacher_id(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    try:

        telegram_id = int(
            message.text.strip()
        )

    except ValueError:

        await message.answer(
            "❌ Telegram ID faqat raqam bo‘lishi kerak."
        )

        return

    await state.update_data(
        telegram_id=telegram_id
    )

    await state.set_state(
        AdminStates.adding_teacher_subject
    )

    await message.answer(
        "📚 O‘qituvchining fanini yozing:"
    )


@router.message(
    AdminStates.adding_teacher_subject
)
async def teacher_subject(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    data = await state.get_data()

    subject = message.text.strip()

    add_teacher(
        data["full_name"],
        data["telegram_id"],
        subject
    )

    await state.clear()

    await message.answer(
        "✅ O‘QITUVCHI QO‘SHILDI!\n\n"
        f"👨‍🏫 F.I.SH: {data['full_name']}\n"
        f"📚 Fan: {subject}\n"
        f"🆔 Telegram ID: {data['telegram_id']}"
    )


# ============================================================
# 📅 DARS JADVALI
# ============================================================

@router.message(F.text == "📅 Dars jadvali")
async def schedule_button(
    message: Message
):

    if not is_admin(message):
        return

    schedules = get_all_schedules()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Jadvalni ko‘rish",
                    callback_data="schedule_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Dars qo‘shish",
                    callback_data="schedule_add"
                )
            ]
        ]
    )

    await message.answer(
        "📅 DARS JADVALI\n\n"
        f"📚 Jami darslar: {len(schedules)} ta\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=keyboard
    )


# ============================================================
# JADVALNI KO'RISH
# ============================================================

@router.callback_query(
    F.data == "schedule_list"
)
async def schedule_list(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    schedules = get_all_schedules()

    if not schedules:

        await callback.message.answer(
            "📅 Hozircha dars jadvali kiritilmagan."
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

    text = "📅 DARS JADVALI\n\n"

    current_day = None

    for lesson in schedules:

        day = lesson["day_of_week"]

        if day != current_day:

            current_day = day

            text += (
                f"\n📌 {day_names.get(day, 'Noma’lum kun')}\n"
            )

        text += (
            f"{lesson['lesson_number']}. "
            f"{lesson['subject']} "
            f"⏰ {lesson['start_time']}"
            f" - {lesson['end_time']}\n"
        )

    await callback.message.answer(
        text
    )

    await callback.answer()


# ============================================================
# DARS QO'SHISH
# ============================================================

@router.callback_query(
    F.data == "schedule_add"
)
async def schedule_add_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):
        return

    await state.set_state(
        AdminStates.adding_schedule_day
    )

    await callback.message.answer(
        "📅 Dars qo‘shish\n\n"
        "Hafta kunini raqamda yozing:\n\n"
        "1 — Dushanba\n"
        "2 — Seshanba\n"
        "3 — Chorshanba\n"
        "4 — Payshanba\n"
        "5 — Juma\n"
        "6 — Shanba"
    )

    await callback.answer()


@router.message(
    AdminStates.adding_schedule_day
)
async def schedule_day(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    try:

        day = int(
            message.text.strip()
        )

        if day < 1 or day > 6:
            raise ValueError

    except ValueError:

        await message.answer(
            "❌ 1 dan 6 gacha bo‘lgan raqam yozing."
        )

        return

    await state.update_data(
        day_of_week=day
    )

    await state.set_state(
        AdminStates.adding_schedule_lesson
    )

    await message.answer(
        "🔢 Dars raqamini yozing:"
    )


@router.message(
    AdminStates.adding_schedule_lesson
)
async def schedule_lesson(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    try:

        lesson = int(
            message.text.strip()
        )

        if lesson < 1:
            raise ValueError

    except ValueError:

        await message.answer(
            "❌ Dars raqamini to‘g‘ri yozing."
        )

        return

    await state.update_data(
        lesson_number=lesson
    )

    await state.set_state(
        AdminStates.adding_schedule_subject
    )

    await message.answer(
        "📚 Fan nomini yozing:"
    )


@router.message(
    AdminStates.adding_schedule_subject
)
async def schedule_subject(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.update_data(
        subject=message.text.strip()
    )

    await state.set_state(
        AdminStates.adding_schedule_start
    )

    await message.answer(
        "⏰ Boshlanish vaqtini yozing.\n"
        "Masalan: 08:00"
    )


@router.message(
    AdminStates.adding_schedule_start
)
async def schedule_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.update_data(
        start_time=message.text.strip()
    )

    await state.set_state(
        AdminStates.adding_schedule_end
    )

    await message.answer(
        "⏰ Tugash vaqtini yozing.\n"
        "Masalan: 08:45"
    )


@router.message(
    AdminStates.adding_schedule_end
)
async def schedule_end(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    data = await state.get_data()

    end_time = message.text.strip()

    add_schedule(
        data["day_of_week"],
        data["lesson_number"],
        data["subject"],
        data["start_time"],
        end_time
    )

    await state.clear()

    await message.answer(
        "✅ DARS JADVALGA QO‘SHILDI!\n\n"
        f"📅 Kun: {data['day_of_week']}\n"
        f"🔢 Dars: {data['lesson_number']}\n"
        f"📚 Fan: {data['subject']}\n"
        f"⏰ {data['start_time']} - {end_time}"
    )


# ============================================================
# 📊 DAVOMAT
# ============================================================
# ============================================================
# 📊 DAVOMAT MENYUSI
# ============================================================

@router.message(F.text == "📊 Davomat")
async def attendance_button(message: Message):

    if not is_admin(message):
        return

    students = get_students()

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        records = get_attendance_by_date(today)
    except Exception as error:

        print("❌ Davomat database xatosi:", repr(error))

        await message.answer(
            "❌ Davomatni ochishda xatolik.\n\n"
            f"{error}"
        )
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Barchasi keldi",
                    callback_data="attendance_all_present"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Kelmaganlarni belgilash",
                    callback_data="attendance_absent_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚠️ Sababli kelmagan",
                    callback_data="attendance_warning_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Bugungi natija",
                    callback_data="attendance_today_result"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 Statistika",
                    callback_data="admin_attendance_stats"
                )
            ]
        ]
    )

    await message.answer(
        "📊 <b>DAVOMAT</b>\n\n"
        f"📅 Sana: <b>{today}</b>\n"
        f"👥 Jami: <b>{len(students)}</b> ta\n\n"
        f"✅ Keldi: <b>{present}</b>\n"
        f"❌ Kelmadi: <b>{absent}</b>\n"
        f"⚠️ Sababli: <b>{warning}</b>\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
# ============================================================
# 📊 DAVOMAT 2.0
# ============================================================
# ============================================================
# ✅ BARCHASI KELDI
# ============================================================

@router.callback_query(
    F.data == "attendance_all_present"
)
async def attendance_all_present(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    today = datetime.now().strftime("%Y-%m-%d")
    students = get_students()

    try:
        records = get_attendance_by_date(today)

        already_marked = {
            record["student_id"]
            for record in records
        }

        added = 0

        for student in students:

            if student["id"] in already_marked:
                continue

            add_attendance(
                student_id=student["id"],
                attendance_date=today,
                status="present",
                lesson_number=None,
                teacher_id=None
            )

            added += 1

        await callback.message.edit_text(
            "✅ <b>BARCHASI KELDI</b>\n\n"
            f"📅 Sana: <b>{today}</b>\n"
            f"👥 Jami: <b>{len(students)}</b> ta\n"
            f"✅ Belgilandi: <b>{added}</b> ta",
            parse_mode="HTML"
        )

        await callback.answer(
            "Davomat saqlandi ✅"
        )

    except Exception as error:

        print(
            "❌ attendance_all_present:",
            repr(error)
        )

        await callback.answer(
            "❌ Saqlashda xatolik!",
            show_alert=True
        )
        # ============================================================
# ❌ KELMAGANLARNI BELGILASH
# ============================================================

@router.callback_query(
    F.data == "attendance_absent_list"
)
async def attendance_absent_list(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    students = get_students()

    if not students:

        await callback.answer(
            "❌ O‘quvchilar yo‘q.",
            show_alert=True
        )

        return

    buttons = []

    for student in students:

        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {student['full_name']}",
                callback_data=f"mark_absent_{student['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Davomat",
            callback_data="attendance_back"
        )
    ])

    await callback.message.edit_text(
        "❌ <b>KELMAGANLARNI BELGILASH</b>\n\n"
        "Kelmagan o‘quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()
    # ============================================================
# ⚠️ SABABLI KELMAGANLAR
# ============================================================

@router.callback_query(
    F.data == "attendance_warning_list"
)
async def attendance_warning_list(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    students = get_students()

    buttons = []

    for student in students:

        buttons.append([
            InlineKeyboardButton(
                text=f"⚠️ {student['full_name']}",
                callback_data=f"mark_warning_{student['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Davomat",
            callback_data="attendance_back"
        )
    ])

    await callback.message.edit_text(
        "⚠️ <b>SABABLI KELMAGANLAR</b>\n\n"
        "O‘quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()
    # ============================================================
# 📋 BUGUNGI NATIJA
# ============================================================

@router.callback_query(
    F.data == "attendance_today_result"
)
async def attendance_today_result(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    today = datetime.now().strftime("%Y-%m-%d")

    students = get_students()
    records = get_attendance_by_date(today)

    present = 0
    absent = 0
    warning = 0

    marked = set()

    for record in records:

        marked.add(
            record["student_id"]
        )

        if record["status"] == "present":
            present += 1

        elif record["status"] == "absent":
            absent += 1

        elif record["status"] == "warning":
            warning += 1

    total = len(students)

    not_marked = max(
        total - len(marked),
        0
    )

    percentage = (
        round(present / total * 100, 1)
        if total else 0
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Davomat",
                    callback_data="attendance_back"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "📋 <b>BUGUNGI DAVOMAT</b>\n\n"
        f"📅 Sana: <b>{today}</b>\n\n"
        f"👥 Jami: <b>{total}</b>\n"
        f"✅ Keldi: <b>{present}</b>\n"
        f"❌ Kelmadi: <b>{absent}</b>\n"
        f"⚠️ Sababli: <b>{warning}</b>\n"
        f"⏳ Belgilanmagan: <b>{not_marked}</b>\n\n"
        f"📈 Davomat: <b>{percentage}%</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()
    # ============================================================
# 📈 STATISTIKA
# ============================================================

@router.callback_query(
    F.data == "admin_attendance_stats"
)
async def admin_attendance_stats(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    today = datetime.now().strftime("%Y-%m-%d")

    records = get_attendance_by_date(today)
    total = len(get_students())

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

    percentage = (
        round(present / total * 100, 1)
        if total else 0
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Davomat",
                    callback_data="attendance_back"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "📈 <b>DAVOMAT STATISTIKASI</b>\n\n"
        f"📅 Sana: <b>{today}</b>\n\n"
        f"👥 Jami: <b>{total}</b>\n"
        f"✅ Keldi: <b>{present}</b>\n"
        f"❌ Kelmadi: <b>{absent}</b>\n"
        f"⚠️ Sababli: <b>{warning}</b>\n\n"
        f"📊 Davomat foizi: <b>{percentage}%</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()
    # ============================================================
# ❌ ABSENT SAQLASH
# ============================================================

@router.callback_query(
    F.data.startswith("mark_absent_")
)
async def mark_student_absent(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    student_id = int(
        callback.data.split("_")[-1]
    )

    student = get_student(student_id)

    if not student:
        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    records = get_attendance_by_date(today)

    already = any(
        r["student_id"] == student_id
        for r in records
    )

    if not already:

        add_attendance(
            student_id=student_id,
            attendance_date=today,
            status="absent",
            lesson_number=None,
            teacher_id=None
        )

    await callback.answer(
        f"❌ {student['full_name']} belgilandi"
    )
    # ============================================================
# ⬅️ DAVOMATGA QAYTISH
# ============================================================

@router.callback_query(
    F.data == "attendance_back"
)
async def attendance_back(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    await callback.message.delete()

    await callback.message.answer(
        "📊 <b>Davomat menyusiga qaytish uchun</b>\n\n"
        "Pastdagi 📊 Davomat tugmasini bosing.",
        parse_mode="HTML"
    )

    await callback.answer()
# ============================================================
# 📝 UY VAZIFALARI
# ============================================================

# ============================================================
# 📝 UY VAZIFALARI
# ============================================================

@router.message(F.text == "📝 Uy vazifalari")
async def homework_button(
    message: Message
):

    if not is_admin(message):
        return

    homework = get_homework()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Uy vazifasi qo‘shish",
                    callback_data="homework_add"
                )
            ],
            [
            InlineKeyboardButton(
                text="📢 Guruhga yuborish",
                callback_data="homework_send_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Uy vazifasini o‘chirish",
                    callback_data="homework_delete_list"
                )
            ]
        ]
    )

    if not homework:

        await message.answer(
            "📝 <b>UY VAZIFALARI</b>\n\n"
            "Hozircha uy vazifalari kiritilmagan.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        return

    text = (
        "📝 <b>UY VAZIFALARI</b>\n\n"
    )

    for item in homework:

        text += (
            f"📚 <b>{item['subject']}</b>\n"
            f"{item['homework_text']}\n"
        )

        if item["due_date"]:

            text += (
                f"📅 Muddat: "
                f"{item['due_date']}\n"
            )

        text += "\n"

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ============================================================
# 📢 UY VAZIFASINI GURUHGA YUBORISH — RO‘YXAT
# ============================================================

@router.callback_query(
    F.data == "homework_send_list"
)
async def homework_send_list(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    homework = get_homework()

    if not homework:

        await callback.answer(
            "📭 Uy vazifalari yo‘q.",
            show_alert=True
        )
        return

    buttons = []

    for item in homework:

        homework_text = str(
            item["homework_text"]
        )

        if len(homework_text) > 30:
            homework_text = (
                homework_text[:30] + "..."
            )

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"📢 {item['subject']} — "
                    f"{homework_text}"
                ),
                callback_data=(
                    f"homework_send_{item['id']}"
                )
            )
        ])

    await callback.message.edit_text(
        "📢 <b>GURUHGA YUBORISH</b>\n\n"
        "Qaysi uy vazifasini guruhga yuborishni "
        "tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 📢 UY VAZIFASINI GURUHGA YUBORISH
# ============================================================

@router.callback_query(
    F.data.startswith("homework_send_")
)
async def homework_send(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    try:

        homework_id = int(
            callback.data.split("_")[-1]
        )

    except (ValueError, TypeError):

        await callback.answer(
            "❌ ID xato.",
            show_alert=True
        )
        return

    homework_list = get_homework()

    homework = None

    for item in homework_list:

        if int(item["id"]) == homework_id:

            homework = item
            break

    if not homework:

        await callback.answer(
            "❌ Uy vazifasi topilmadi.",
            show_alert=True
        )
        return

    group_id = get_group_id()

    if not group_id:

        await callback.answer(
            "❌ Guruh ID o‘rnatilmagan.",
            show_alert=True
        )
        return

    try:

        due_date = (
            homework["due_date"]
            or "Muddat belgilanmagan"
        )

        await callback.bot.send_message(
            group_id,
            "📚 <b>UY VAZIFASI</b>\n\n"
            f"📖 Fan: <b>{homework['subject']}</b>\n\n"
            f"📝 Vazifa:\n"
            f"<b>{homework['homework_text']}</b>\n\n"
            f"📅 Muddat: <b>{due_date}</b>\n\n"
            "🎒 Vazifani vaqtida bajarishni unutmang!",
            parse_mode="HTML"
        )

    except Exception as error:

        print(
            "❌ HOMEWORK SEND XATOSI:",
            repr(error)
        )

        await callback.answer(
            "❌ Guruhga yuborishda xatolik.",
            show_alert=True
        )
        return

    await callback.answer(
        "📢 Guruhga yuborildi! ✅",
        show_alert=True
    )

    await callback.message.edit_text(
        "✅ <b>UY VAZIFASI GURUHGA YUBORILDI!</b>\n\n"
        f"📚 Fan: <b>{homework['subject']}</b>\n"
        f"📝 {homework['homework_text']}\n"
        f"📅 Muddat: <b>"
        f"{homework['due_date'] or 'Belgilanmagan'}"
        f"</b>",
        parse_mode="HTML"
    )
# ============================================================
# 🗑 UY VAZIFASINI O‘CHIRISH — RO‘YXAT
# ============================================================

@router.callback_query(
    F.data == "homework_delete_list"
)
async def homework_delete_list(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    homework = get_homework()

    if not homework:

        await callback.answer(
            "📭 O‘chirish uchun uy vazifalari yo‘q.",
            show_alert=True
        )

        return

    buttons = []

    for item in homework:

        homework_text = str(
            item["homework_text"]
        )

        if len(homework_text) > 30:
            homework_text = (
                homework_text[:30] + "..."
            )

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"🗑 {item['subject']} — "
                    f"{homework_text}"
                ),
                callback_data=(
                    f"homework_delete_{item['id']}"
                )
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="homework_delete_back"
        )
    ])

    await callback.message.edit_text(
        "🗑 <b>UY VAZIFASINI O‘CHIRISH</b>\n\n"
        "O‘chirmoqchi bo‘lgan vazifani tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()
    # ============================================================
# 🗑 UY VAZIFASINI O‘CHIRISH
# ============================================================

@router.callback_query(
    F.data.startswith("homework_delete_")
)
async def homework_delete(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    try:

        homework_id = int(
            callback.data.split("_")[-1]
        )

    except (ValueError, TypeError):

        await callback.answer(
            "❌ Uy vazifasi ID xato.",
            show_alert=True
        )

        return

    try:

        deleted = delete_homework(
            homework_id
        )

    except Exception as error:

        print(
            "❌ HOMEWORK DELETE XATOSI:",
            repr(error)
        )

        await callback.answer(
            "❌ O‘chirishda xatolik.",
            show_alert=True
        )

        return

    if not deleted:

        await callback.answer(
            "❌ Uy vazifasi topilmadi.",
            show_alert=True
        )

        return

    await callback.answer(
        "🗑 Uy vazifasi o‘chirildi!"
    )

    homework = get_homework()

    if not homework:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Uy vazifasi qo‘shish",
                        callback_data="homework_add"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "📝 <b>UY VAZIFALARI</b>\n\n"
            "📭 Hozircha uy vazifalari yo‘q.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        return

    buttons = []

    for item in homework:

        homework_text = str(
            item["homework_text"]
        )

        if len(homework_text) > 30:
            homework_text = (
                homework_text[:30] + "..."
            )

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"🗑 {item['subject']} — "
                    f"{homework_text}"
                ),
                callback_data=(
                    f"homework_delete_{item['id']}"
                )
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="homework_delete_back"
        )
    ])

    await callback.message.edit_text(
        "🗑 <b>UY VAZIFASINI O‘CHIRISH</b>\n\n"
        "O‘chirmoqchi bo‘lgan vazifani tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

# ============================================================
# ➕ UY VAZIFASI QO‘SHISHNI BOSHLASH
# ============================================================

@router.callback_query(
    F.data == "homework_add"
)
async def homework_add_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):

        await callback.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )

        return

    await state.set_state(
        HomeworkStates.subject
    )

    await callback.message.answer(
        "➕ <b>UY VAZIFASI QO‘SHISH</b>\n\n"
        "📚 Fan nomini yozing.\n\n"
        "Masalan:\n"
        "<b>Matematika</b>",
        parse_mode="HTML"
    )

    await callback.answer()
# ============================================================
# 📚 FAN
# ============================================================

@router.message(
    HomeworkStates.subject
)
async def homework_subject(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    subject = message.text.strip()

    if not subject:
        await message.answer(
            "❌ Fan nomi bo‘sh bo‘lmasin."
        )
        return

    await state.update_data(
        subject=subject
    )

    await state.set_state(
        HomeworkStates.homework_text
    )

    await message.answer(
        "📝 <b>Uy vazifasini yozing:</b>\n\n"
        "Masalan:\n"
        "<i>12-mashq, 15-bet</i>",
        parse_mode="HTML"
    )


# ============================================================
# 📝 UY VAZIFASI MATNI
# ============================================================

@router.message(
    HomeworkStates.homework_text
)
async def homework_text(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    homework_text = message.text.strip()

    if not homework_text:
        await message.answer(
            "❌ Uy vazifasi bo‘sh bo‘lmasin."
        )
        return

    await state.update_data(
        homework_text=homework_text
    )

    await state.set_state(
        HomeworkStates.due_date
    )

    await message.answer(
        "📅 <b>Vazifa muddatini yozing:</b>\n\n"
        "Masalan:\n"
        "<code>25.08.2026</code>\n\n"
        "Agar muddat bo‘lmasa:\n"
        "<code>yo‘q</code>",
        parse_mode="HTML"
    )


# ============================================================
# 📅 MUDDAT VA SAQLASH
# ============================================================

@router.message(
    HomeworkStates.due_date
)
async def homework_due_date(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    due_date = message.text.strip()

    if due_date.lower() in (
        "yo‘q",
        "yo'q",
        "yoq",
        "-"
    ):
        due_date = None

    data = await state.get_data()

    try:

        homework_id = add_homework(
            subject=data["subject"],
            homework_text=data["homework_text"],
            due_date=due_date,
            teacher_id=None
        )

    except Exception as error:

        print(
            "❌ HOMEWORK SAQLASH XATOSI:",
            repr(error)
        )

        await message.answer(
            "❌ Uy vazifasini saqlashda xatolik.\n\n"
            f"<code>{escape(str(error))}</code>",
            parse_mode="HTML"
        )

        await state.clear()
        return

    await state.clear()

    due_text = (
        due_date
        if due_date
        else "Muddat belgilanmagan"
    )

    await message.answer(
        "✅ <b>UY VAZIFASI SAQLANDI!</b>\n\n"
        f"📚 Fan: <b>{escape(data['subject'])}</b>\n"
        f"📝 Vazifa: <b>{escape(data['homework_text'])}</b>\n"
        f"📅 Muddat: <b>{escape(str(due_text))}</b>\n\n"
        f"🆔 ID: <code>{homework_id}</code>",
        parse_mode="HTML"
    )

# ============================================================
# ⭐ BAHOLAR
# ============================================================

# ============================================================
# ⭐ BAHOLAR
# ============================================================

@router.message(F.text == "⭐ Baholar")
async def grades_button(message: Message):

    if not is_admin(message):
        return

    students = get_students()

    if not students:
        await message.answer(
            "❌ O‘quvchilar bazasi bo‘sh."
        )
        return

    buttons = []

    for student in students:

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {student['full_name']}",
                callback_data=f"grade_student_{student['id']}"
            )
        ])

    await message.answer(
        "⭐ **BAHOLARNI BOSHQARISH**\n\n"
        f"👥 Jami o‘quvchilar: {len(students)} ta\n\n"
        "Baho qo‘yish uchun o‘quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="Markdown"
    )


# ============================================================
# O'QUVCHI TANLANDI
# ============================================================

@router.callback_query(
    F.data.startswith("grade_student_")
)
async def grade_student_selected(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    student_id = int(
        callback.data.split("_")[-1]
    )

    student = get_student(
        student_id
    )

    if not student:
        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📐 Matematika",
                    callback_data=f"grade_subject_{student_id}_Matematika"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Ona tili",
                    callback_data=f"grade_subject_{student_id}_Ona_tili"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇬🇧 Ingliz tili",
                    callback_data=f"grade_subject_{student_id}_Ingliz_tili"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧪 Fizika",
                    callback_data=f"grade_subject_{student_id}_Fizika"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧬 Biologiya",
                    callback_data=f"grade_subject_{student_id}_Biologiya"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📖 Tarix",
                    callback_data=f"grade_subject_{student_id}_Tarix"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗺 Geografiya",
                    callback_data=f"grade_subject_{student_id}_Geografiya"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="grades_back_students"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "⭐ **BAHO QO‘YISH**\n\n"
        f"👤 {student['full_name']}\n\n"
        "📚 Fanni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    await callback.answer()


# ============================================================
# FAN TANLANDI
# ============================================================

@router.callback_query(
    F.data.startswith("grade_subject_")
)
async def grade_subject_selected(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    parts = callback.data.split("_")

    student_id = int(parts[2])

    subject = "_".join(parts[3:])

    student = get_student(
        student_id
    )

    if not student:
        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1️⃣",
                    callback_data=f"save_grade_{student_id}_{subject}_1"
                ),
                InlineKeyboardButton(
                    text="2️⃣",
                    callback_data=f"save_grade_{student_id}_{subject}_2"
                ),
                InlineKeyboardButton(
                    text="3️⃣",
                    callback_data=f"save_grade_{student_id}_{subject}_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text="4️⃣",
                    callback_data=f"save_grade_{student_id}_{subject}_4"
                ),
                InlineKeyboardButton(
                    text="5️⃣",
                    callback_data=f"save_grade_{student_id}_{subject}_5"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Fanlar",
                    callback_data=f"grade_student_{student_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "⭐ **BAHO TANLASH**\n\n"
        f"👤 {student['full_name']}\n"
        f"📚 Fan: {subject.replace('_', ' ')}\n\n"
        "Baho tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

    await callback.answer()


# ============================================================
# BAHONI SAQLASH
# ============================================================

@router.callback_query(
    F.data.startswith("save_grade_")
)
async def save_grade_handler(
    callback: CallbackQuery
):
    if not is_admin_callback(callback):
        return

    try:
        parts = callback.data.split("_")
        student_id = int(parts[2])
        grade = int(parts[-1])
        subject = "_".join(parts[3:-1]).replace("_", " ").strip()
    except (ValueError, TypeError):
        await callback.answer(
            "❌ Baho ma’lumotlari xato.",
            show_alert=True
        )
        return

    if grade not in (1, 2, 3, 4, 5):
        await callback.answer(
            "❌ Baho 1 dan 5 gacha bo‘lishi kerak.",
            show_alert=True
        )
        return

    student = get_student(student_id)

    if not student:
        await callback.answer(
            "❌ O‘quvchi topilmadi.",
            show_alert=True
        )
        return

    try:
        # database.py dagi haqiqiy signature:
        # add_grade(student_id, subject, grade, teacher_id, grade_date, comment)
        add_grade(
            student_id=student_id,
            subject=subject,
            grade=grade,
            teacher_id=None,
            grade_date=datetime.now().strftime("%Y-%m-%d"),
            comment=None
        )

    except Exception as error:
        print("❌ BAHO SAQLASH XATOSI:", repr(error))

        await callback.message.answer(
            "❌ Bahoni saqlashda xatolik.\n\n"
            f"<code>{escape(str(error))}</code>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Yana baho qo‘yish",
                    callback_data=f"grade_student_{student_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 O‘quvchi baholarini ko‘rish",
                    callback_data=f"profile_grades_{student_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ O‘quvchilar",
                    callback_data="grades_back_students"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "✅ <b>BAHO SAQLANDI!</b>\n\n"
        f"👤 <b>{escape(str(student['full_name']))}</b>\n"
        f"📚 Fan: <b>{escape(subject)}</b>\n"
        f"⭐ Baho: <b>{grade}</b>\n"
        f"📅 Sana: <b>{datetime.now().strftime('%Y-%m-%d')}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer("Baho saqlandi ✅")


# ============================================================
# ORQAGA — O'QUVCHILAR
# ============================================================

@router.callback_query(
    F.data == "grades_back_students"
)
async def grades_back_students(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    students = get_students()

    buttons = []

    for student in students:

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {student['full_name']}",
                callback_data=f"grade_student_{student['id']}"
            )
        ])

    await callback.message.edit_text(
        "⭐ **BAHOLARNI BOSHQARISH**\n\n"
        "O‘quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="Markdown"
    )

    await callback.answer()

# ============================================================
# 🏆 REYTING
# ============================================================
# ============================================================
# 🏆 REYTING
# ============================================================

@router.message(F.text == "🏆 Reyting")
async def ranking_button(message: Message):

    if not is_admin(message):
        return

    students = get_students()

    if not students:

        await message.answer(
            "❌ O‘quvchilar bazasi bo‘sh."
        )

        return

    ranking = []

    for student in students:

        try:
            grades = get_student_grades(
                student["id"]
            )
        except Exception:
            grades = []

        total = 0
        count = 0

        for grade in grades:

            try:
                value = grade["grade"]
            except (KeyError, TypeError, IndexError):

                try:
                    value = grade[1]
                except (IndexError, TypeError):
                    continue

            try:
                value = float(value)

                total += value
                count += 1

            except (ValueError, TypeError):
                continue

        if count > 0:

            average = round(
                total / count,
                2
            )

        else:

            average = 0

        ranking.append({
            "full_name": student["full_name"],
            "average": average,
            "count": count
        })

    # Eng yuqori bahodan pastga
    ranking.sort(
        key=lambda x: x["average"],
        reverse=True
    )

    text = (
        "🏆 <b>9-E REYTING</b>\n\n"
    )

    position = 0

    for index, student in enumerate(
        ranking,
        start=1
    ):

        # Bahosi yo‘q o‘quvchilarni oxiriga
        if student["count"] == 0:
            continue

        position += 1

        if position == 1:
            medal = "🥇"

        elif position == 2:
            medal = "🥈"

        elif position == 3:
            medal = "🥉"

        else:
            medal = f"{position}."

        text += (
            f"{medal} "
            f"<b>{student['full_name']}</b>\n"
            f"⭐ O‘rtacha: "
            f"<b>{student['average']}</b>\n"
            f"📚 Baholar: {student['count']} ta\n\n"
        )

    if position == 0:

        text += (
            "📭 Hozircha hech bir "
            "o‘quvchiga baho qo‘yilmagan."
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# ============================================================
# 📢 E'LONLAR — PRO
# ============================================================

# Oxirgi yuborilgan Telegram message ID'lari.
# Bot qayta ishga tushsa bu ma'lumot tozalanadi.
announcement_message_ids = {}


def normalize_button_text(text):
    if not text:
        return ""

    return (
        text
        .replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .strip()
    )


# ============================================================
# 📢 E'LONLAR MENYUSI
# ============================================================

@router.message(F.text.in_({"📢 E'lonlar", "📢 E’lonlar"}))
async def announcements_button(message: Message):

    if not is_admin(message):
        return

    text = normalize_button_text(
        message.text
    )

    if text not in ("📢 E'lonlar", "📢 E’lonlar"):
        return

    try:
        announcements = get_announcements()

    except Exception as error:

        print(
            "❌ E'lonlar database xatosi:",
            repr(error)
        )

        await message.answer(
            "❌ E'lonlar bo‘limini ochishda xatolik.\n\n"
            f"{escape(str(error))}",
            parse_mode="HTML"
        )
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
            ]
        ]
    )

    await message.answer(
        "📢 <b>E'LONLAR</b>\n\n"
        f"📊 Saqlangan e'lonlar: "
        f"<b>{len(announcements)}</b> ta\n\n"
        "Kerakli amalni tanlang:",
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

        await callback.answer(
            "⛔ Ruxsat yo‘q.",
            show_alert=True
        )
        return

    await state.clear()

    await state.set_state(
        AdminStates.announcement_title
    )

    await callback.message.answer(
        "📢 <b>YANGI E'LON</b>\n\n"
        "1️⃣ E'lon sarlavhasini yozing.\n\n"
        "Masalan:\n"
        "<i>Ertangi kun uchun muhim xabar</i>",
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 📝 E'LON SARLAVHASI
# ============================================================

@router.message(
    AdminStates.announcement_title
)
async def announcement_title(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    title = (
        message.text or ""
    ).strip()

    if not title:

        await message.answer(
            "❌ Sarlavha bo‘sh bo‘lishi mumkin emas."
        )
        return

    await state.update_data(
        announcement_title=title
    )

    await state.set_state(
        AdminStates.announcement_text
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
    AdminStates.announcement_text
)
async def announcement_text(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    announcement_text_value = (
        message.text or ""
    ).strip()

    if not announcement_text_value:

        await message.answer(
            "❌ E'lon matni bo‘sh bo‘lishi mumkin emas."
        )
        return

    data = await state.get_data()

    title = data.get(
        "announcement_title"
    )

    if not title:

        await message.answer(
            "❌ E'lon sarlavhasi topilmadi."
        )

        await state.clear()
        return

    await state.update_data(
        announcement_text=announcement_text_value
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Guruhga yuborish",
                    callback_data="announcement_send"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💾 Faqat saqlash",
                    callback_data="announcement_save"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="announcement_cancel"
                )
            ]
        ]
    )

    await message.answer(
        "👀 <b>E'LONNI TEKSHIRING</b>\n\n"
        f"📢 <b>{escape(title)}</b>\n\n"
        f"{escape(announcement_text_value)}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ============================================================
# 💾 FAQAT SAQLASH
# ============================================================

@router.callback_query(
    F.data == "announcement_save"
)
async def announcement_save(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin_callback(callback):
        return

    data = await state.get_data()

    title = data.get(
        "announcement_title"
    )

    announcement_text_value = data.get(
        "announcement_text"
    )

    if not title or not announcement_text_value:

        await callback.answer(
            "❌ E'lon ma'lumotlari topilmadi.",
            show_alert=True
        )

        await state.clear()
        return

    try:

        announcement_id = add_announcement(
            title=title,
            text=announcement_text_value,
            created_by=callback.from_user.id,
            is_pinned=0
        )

    except Exception as error:

        print(
            "❌ E'lon saqlash xatosi:",
            repr(error)
        )

        await callback.message.answer(
            "❌ E'lonni saqlashda xatolik.\n\n"
            f"<code>{escape(str(error))}</code>",
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await state.clear()

    await callback.message.edit_text(
        "✅ <b>E'LON SAQLANDI!</b>\n\n"
        f"🆔 ID: <code>{announcement_id}</code>\n"
        f"📢 <b>{escape(title)}</b>\n\n"
        f"{escape(announcement_text_value)}",
        parse_mode="HTML"
    )

    await callback.answer(
        "E'lon saqlandi ✅"
    )


# ============================================================
# 📤 YANGI E'LONNI GURUHGA YUBORISH
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

    title = data.get(
        "announcement_title"
    )

    announcement_text_value = data.get(
        "announcement_text"
    )

    if not title or not announcement_text_value:

        await callback.answer(
            "❌ E'lon ma'lumotlari topilmadi.",
            show_alert=True
        )

        await state.clear()
        return

    group_id = get_group_id()

    if not group_id:

        await callback.message.answer(
            "❌ <b>GURUH ID TOPILMADI</b>\n\n"
            "Avval e'lon yuboriladigan guruhda:\n\n"
            "<code>/setgroup</code>\n\n"
            "komandasini yuboring.",
            parse_mode="HTML"
        )

        await callback.answer()
        return

    try:

        telegram_message = await callback.bot.send_message(
            chat_id=int(group_id),
            text=(
                "📢 <b>E'LON</b>\n\n"
                f"🔔 <b>{escape(title)}</b>\n\n"
                f"{escape(announcement_text_value)}\n\n"
                "🏫 <b>9-E sinf</b>"
            ),
            parse_mode="HTML"
        )

        announcement_id = add_announcement(
            title=title,
            text=announcement_text_value,
            created_by=callback.from_user.id,
            is_pinned=0
        )

        announcement_message_ids[
            int(announcement_id)
        ] = telegram_message.message_id

    except Exception as error:

        print(
            "❌ E'lon yuborish xatosi:",
            repr(error)
        )

        await callback.message.answer(
            "❌ E'lonni guruhga yuborishda xatolik.\n\n"
            f"<code>{escape(str(error))}</code>",
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await state.clear()

    await callback.message.edit_text(
        "✅ <b>E'LON GURUHGA YUBORILDI!</b>\n\n"
        f"📢 <b>{escape(title)}</b>\n\n"
        f"{escape(announcement_text_value)}",
        parse_mode="HTML"
    )

    await callback.answer(
        "📢 Guruhga yuborildi! ✅"
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

    await show_announcement_history(
        callback
    )

    await callback.answer()


async def show_announcement_history(
    callback: CallbackQuery
):

    try:

        announcements = get_announcements()

    except Exception as error:

        print(
            "❌ E'lonlar tarix xatosi:",
            repr(error)
        )

        await callback.message.edit_text(
            "❌ <b>E'lonlar tarixini ochishda xatolik.</b>\n\n"
            f"<code>{escape(str(error))}</code>",
            parse_mode="HTML"
        )
        return

    if not announcements:

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
                        text="⬅️ Orqaga",
                        callback_data="announcement_back"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "📋 <b>E'LONLAR TARIXI</b>\n\n"
            "📭 Hozircha e'lonlar yo‘q.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        return

    text = (
        "📋 <b>E'LONLAR TARIXI</b>\n\n"
    )

    buttons = []

    for index, item in enumerate(
        announcements,
        start=1
    ):

        announcement_id = int(
            item["id"]
        )

        title = str(
            item["title"]
        )

        announcement_text_value = str(
            item["text"]
        )

        pinned = ""

        try:
            if item["is_pinned"]:
                pinned = " 📌"
        except Exception:
            pass

        text += (
            f"<b>{index}. 📢 "
            f"{escape(title)}{pinned}</b>\n"
            f"{escape(announcement_text_value)}\n\n"
        )

        row = [
            InlineKeyboardButton(
                text=f"📢 {index}",
                callback_data=(
                    f"announcement_resend_{announcement_id}"
                )
            ),
            InlineKeyboardButton(
                text=f"🗑 {index}",
                callback_data=(
                    f"announcement_delete_{announcement_id}"
                )
            )
        ]

        buttons.append(row)

        if (
            announcement_id
            in announcement_message_ids
        ):

            buttons.append([
                InlineKeyboardButton(
                    text=f"📌 {index}-e'lonni pin",
                    callback_data=(
                        f"announcement_pin_{announcement_id}"
                    )
                )
            ])

        if len(text) > 3500:
            text += "..."
            break

    buttons.append([
        InlineKeyboardButton(
            text="➕ Yangi e'lon",
            callback_data="announcement_new"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="announcement_back"
        )
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )


# ============================================================
# 🔄 E'LONNI QAYTA GURUHGA YUBORISH
# ============================================================

@router.callback_query(
    F.data.startswith("announcement_resend_")
)
async def announcement_resend(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    try:

        announcement_id = int(
            callback.data.split("_")[-1]
        )

    except (ValueError, TypeError):

        await callback.answer(
            "❌ E'lon ID xato.",
            show_alert=True
        )
        return

    try:

        announcements = get_announcements()

        announcement = None

        for item in announcements:

            if int(item["id"]) == announcement_id:
                announcement = item
                break

        if not announcement:

            await callback.answer(
                "❌ E'lon topilmadi.",
                show_alert=True
            )
            return

        group_id = get_group_id()

        if not group_id:

            await callback.answer(
                "❌ Guruh ID o‘rnatilmagan.",
                show_alert=True
            )
            return

        telegram_message = (
            await callback.bot.send_message(
                chat_id=int(group_id),
                text=(
                    "📢 <b>E'LON</b>\n\n"
                    f"🔔 <b>{escape(str(announcement['title']))}</b>\n\n"
                    f"{escape(str(announcement['text']))}\n\n"
                    "🏫 <b>9-E sinf</b>"
                ),
                parse_mode="HTML"
            )
        )

        announcement_message_ids[
            announcement_id
        ] = telegram_message.message_id

    except Exception as error:

        print(
            "❌ E'lonni qayta yuborish xatosi:",
            repr(error)
        )

        await callback.answer(
            "❌ Guruhga yuborilmadi.",
            show_alert=True
        )
        return

    await callback.answer(
        "📢 Guruhga yuborildi! ✅",
        show_alert=True
    )


# ============================================================
# 📌 E'LONNI PIN QILISH
# ============================================================

@router.callback_query(
    F.data.startswith("announcement_pin_")
)
async def announcement_pin(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    try:

        announcement_id = int(
            callback.data.split("_")[-1]
        )

    except (ValueError, TypeError):

        await callback.answer(
            "❌ E'lon ID xato.",
            show_alert=True
        )
        return

    group_id = get_group_id()

    if not group_id:

        await callback.answer(
            "❌ Guruh ID o‘rnatilmagan.",
            show_alert=True
        )
        return

    message_id = (
        announcement_message_ids.get(
            announcement_id
        )
    )

    if not message_id:

        await callback.answer(
            "⚠️ Bu e'lonning Telegram xabari topilmadi. "
            "Avval 📢 qayta yuboring.",
            show_alert=True
        )
        return

    try:

        await callback.bot.pin_chat_message(
            chat_id=int(group_id),
            message_id=int(message_id),
            disable_notification=False
        )

    except Exception as error:

        print(
            "❌ E'lonni pin qilish xatosi:",
            repr(error)
        )

        await callback.answer(
            "❌ Pin qilishda xatolik. "
            "Botga guruhda xabarlarni pin qilish huquqini bering.",
            show_alert=True
        )
        return

    await callback.answer(
        "📌 E'lon guruhda mahkamlandi! ✅",
        show_alert=True
    )


# ============================================================
# 🗑 E'LONNI O'CHIRISH
# ============================================================

@router.callback_query(
    F.data.startswith("announcement_delete_")
)
async def announcement_delete(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    try:

        announcement_id = int(
            callback.data.split("_")[-1]
        )

    except (ValueError, TypeError):

        await callback.answer(
            "❌ E'lon ID xato.",
            show_alert=True
        )
        return

    try:

        deleted = delete_announcement(
            announcement_id
        )

    except Exception as error:

        print(
            "❌ E'lon o‘chirish xatosi:",
            repr(error)
        )

        await callback.answer(
            "❌ O‘chirishda xatolik.",
            show_alert=True
        )
        return

    if not deleted:

        await callback.answer(
            "❌ E'lon topilmadi.",
            show_alert=True
        )
        return

    announcement_message_ids.pop(
        announcement_id,
        None
    )

    await callback.answer(
        "🗑 E'lon o‘chirildi! ✅",
        show_alert=True
    )

    await show_announcement_history(
        callback
    )


# ============================================================
# ⬅️ E'LONLAR ORQAGA
# ============================================================

@router.callback_query(
    F.data == "announcement_back"
)
async def announcement_back(
    callback: CallbackQuery
):

    if not is_admin_callback(callback):
        return

    await callback.message.edit_text(
        "📢 <b>E'LONLAR</b>\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=InlineKeyboardMarkup(
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
                ]
            ]
        ),
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
        "❌ <b>E'lon yaratish bekor qilindi.</b>",
        parse_mode="HTML"
    )

    await callback.answer(
        "Bekor qilindi"
    )


# ============================================================
# 🎉 BAYRAMLAR
# ============================================================


# ============================================================
# 🎂 TUG'ILGAN KUNLAR
# ============================================================


# ============================================================
# 🎂 TUG'ILGAN KUNLAR
# ============================================================

@router.message(F.text.in_({"🎂 Tug‘ilgan kunlar", "🎂 Tug'ilgan kunlar"}))
async def birthdays_button(message: Message):
    if not is_admin(message):
        return

    students = get_students()

    if not students:
        await message.answer(
            "🎂 O‘quvchilar bazasi bo‘sh."
        )
        return

    today = datetime.now().strftime("%m-%d")
    birthdays = []

    for student in students:
        birth_date = student["birth_date"]

        if not birth_date:
            continue

        parsed = None

        for fmt in (
            "%d.%m.%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d.%m.%y",
        ):
            try:
                parsed = datetime.strptime(
                    str(birth_date).strip(),
                    fmt
                )
                break
            except ValueError:
                continue

        if parsed and parsed.strftime("%m-%d") == today:
            birthdays.append(
                student["full_name"]
            )

    if not birthdays:
        await message.answer(
            "🎂 Bugun tug‘ilgan kuni "
            "bo‘lgan o‘quvchi yo‘q."
        )
        return

    text = (
        "🎂 BUGUNGI TUG‘ILGAN KUNLAR\n\n"
    )

    for name in birthdays:
        text += f"🎉 {name}\n"

    await message.answer(text)

# ============================================================
# 📸 TADBIRLAR
# ============================================================

@router.message(F.text == "📸 Tadbirlar")
async def events_button(message: Message):
    if not is_admin(message):
        return

    await message.answer(
        "📸 <b>TADBIRLAR</b>\n\n"
        "Bu bo‘lim orqali sinf tadbirlarini boshqarish mumkin.\n\n"
        "🔧 Tadbirlar boshqaruvi tayyorlanmoqda.",
        parse_mode="HTML"
    )


# ============================================================
# ⚙️ SOZLAMALAR
# ============================================================

@router.message(F.text == "⚙️ Sozlamalar")
async def settings_button(message: Message):
    if not is_admin(message):
        return

    await message.answer(
        "⚙️ <b>SOZLAMALAR</b>\n\n"
        "🏫 9-E SCHOOL BOT\n"
        "🤖 Bot sozlamalari bo‘limi.\n\n"
        "✅ Bot ishlayapti.",
        parse_mode="HTML"
    )

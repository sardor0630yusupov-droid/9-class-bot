# ============================================================
# 9-E SCHOOL BOT — SCHEDULER
# ============================================================

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from html import escape

from aiogram import Bot

from database import (
    get_schedule,
    get_homework,
    get_student,
    get_student_grades,
    get_announcements,
    get_attendance_by_date,
    get_students,
)


# ============================================================
# 🇺🇿 O'ZBEKISTON VAQTI
# ============================================================

UZBEKISTAN_TZ = ZoneInfo("Asia/Tashkent")

GROUP_FILE = "data/group_id.txt"


# ============================================================
# 👥 GURUH ID
# ============================================================

def get_group_id():

    try:

        with open(
            GROUP_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return int(
                file.read().strip()
            )

    except Exception:

        return None


def save_group_id(
    group_id
):

    with open(
        GROUP_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            str(group_id)
        )


# ============================================================
# 📅 HAFTA KUNI
# ============================================================

def python_weekday_to_school_day(
    weekday
):

    if weekday == 6:
        return None

    return weekday + 1


def tomorrow_school_day(
    now
):

    tomorrow = (
        now + timedelta(days=1)
    )

    return python_weekday_to_school_day(
        tomorrow.weekday()
    )


# ============================================================
# 📚 ERTANGI DARS JADVALI — GURUH
# ============================================================

async def send_tomorrow_schedule(
    bot: Bot
):

    group_id = get_group_id()

    if not group_id:

        print(
            "⚠️ Guruh ID hali o‘rnatilmagan."
        )

        return

    now = datetime.now(
        UZBEKISTAN_TZ
    )

    tomorrow = (
        now + timedelta(days=1)
    )

    school_day = (
        python_weekday_to_school_day(
            tomorrow.weekday()
        )
    )

    if school_day is None:

        await bot.send_message(
            group_id,
            "🌙 <b>Ertaga yakshanba!</b>\n\n"
            "🏫 9-E sinf uchun ertaga maktab yo‘q.\n"
            "Dam olish kuningiz maroqli o‘tsin! 😊",
            parse_mode="HTML"
        )

        return

    schedules = get_schedule(
        school_day
    )

    day_names = {
        1: "Dushanba",
        2: "Seshanba",
        3: "Chorshanba",
        4: "Payshanba",
        5: "Juma",
        6: "Shanba"
    }

    day_name = day_names[
        school_day
    ]

    if not schedules:

        await bot.send_message(
            group_id,
            f"📢 <b>Ertaga — {day_name}</b>\n\n"
            "📚 9-E sinf uchun dars jadvali "
            "hali kiritilmagan.",
            parse_mode="HTML"
        )

        return

    text = (
        "📚 <b>ERTANGI DARS JADVALI</b>\n\n"
        "🏫 9-E sinf\n"
        f"📅 {day_name}\n\n"
    )

    for schedule in schedules:

        text += (
            f"{schedule['lesson_number']}️⃣ "
            f"<b>{escape(str(schedule['subject']))}</b>\n"
            f"⏰ {schedule['start_time']}–"
            f"{schedule['end_time']}\n\n"
        )

    text += (
        "🎒 Ertaga forma va kitoblaringizni "
        "to‘liq qilib olib kelishni unutmang!"
    )

    await bot.send_message(
        group_id,
        text,
        parse_mode="HTML"
    )


# ============================================================
# 🔔 DARS — 10 DAQIQA OLDIN
# ============================================================

async def send_lesson_reminder(
    bot: Bot,
    schedule
):

    group_id = get_group_id()

    if not group_id:
        return

    await bot.send_message(
        group_id,
        "🔔 <b>DARS BOSHLANISHIGA 10 DAQIQA QOLDI!</b>\n\n"
        f"📚 Fan: <b>{escape(str(schedule['subject']))}</b>\n"
        f"⏰ Boshlanishi: "
        f"<b>{escape(str(schedule['start_time']))}</b>\n"
        "🏫 9-E sinf\n\n"
        "📖 Darsga tayyorlanib oling!",
        parse_mode="HTML"
    )


# ============================================================
# 📝 UY VAZIFASI — GURUHGA
# ============================================================

async def send_homework_reminder(
    bot: Bot,
    homework
):

    group_id = get_group_id()

    if not group_id:
        return

    subject = escape(
        str(homework["subject"])
    )

    homework_text = escape(
        str(homework["homework_text"])
    )

    due_date = escape(
        str(homework["due_date"])
    )

    await bot.send_message(
        group_id,
        "🔔 <b>UY VAZIFASI ESLATMASI</b>\n\n"
        f"📚 Fan: <b>{subject}</b>\n"
        f"📝 Vazifa: <b>{homework_text}</b>\n"
        f"📅 Muddat: <b>{due_date}</b>\n\n"
        "🎒 Uy vazifangizni bajarishni unutmang!",
        parse_mode="HTML"
    )


# ============================================================
# 🎂 BUGUN TUG‘ILGAN KUNLAR
# ============================================================

async def send_birthday_notifications(bot: Bot, current_date, sent_birthdays):
    group_id = get_group_id()
    if not group_id:
        return
    try:
        students = get_students()
    except Exception as error:
        print("❌ Tug‘ilgan kunlarni olish xatosi:", repr(error))
        return
    today = current_date.strftime("%m-%d")
    for student in students:
        birth_date = student["birth_date"]
        if not birth_date:
            continue
        birth_text = str(birth_date).strip()
        month_day = None
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y.%m.%d"):
            try:
                month_day = datetime.strptime(birth_text, fmt).strftime("%m-%d")
                break
            except ValueError:
                pass
        if month_day != today:
            continue
        key = (current_date, int(student["id"]))
        if key in sent_birthdays:
            continue
        name = escape(str(student["full_name"]))
        text = (
            "🎂 <b>TUG‘ILGAN KUN!</b>\n\n"
            f"🎉 Bugun <b>{name}</b>ning tug‘ilgan kuni!\n\n"
            "🎈 Tug‘ilgan kuningiz muborak bo‘lsin!\n"
            "Sizga sog‘liq, baxt, a’lo baholar va katta muvaffaqiyatlar tilaymiz! 🥳🎁\n\n"
            "🏫 <b>9-E sinf</b>"
        )
        try:
            await bot.send_message(group_id, text, parse_mode="HTML")
            sent_birthdays.add(key)
        except Exception as error:
            print("❌ Tug‘ilgan kun xabari yuborilmadi:", repr(error))


# ============================================================
# ⏰ ASOSIY SCHEDULER
# ============================================================

async def scheduler_loop(
    bot: Bot
):

    print(
        "⏰ Avtomatik scheduler ishga tushdi!"
    )

    last_schedule_message = None

    sent_reminders = set()
    sent_birthdays = set()





    while True:

        try:

            now = datetime.now(
                UZBEKISTAN_TZ
            )

            current_date = (
                now.date()
            )

            current_time = (
                now.strftime("%H:%M")
            )

            await send_birthday_notifications(
                bot,
                current_date,
                sent_birthdays
            )

            # =================================================
            # 📚 19:00 — GURUHGA ERTANGI JADVAL
            # =================================================

            schedule_key = (
                current_date,
                "tomorrow_schedule"
            )

            if (
                current_time == "19:00"
                and
                last_schedule_message
                != schedule_key
            ):

                await send_tomorrow_schedule(
                    bot
                )

                last_schedule_message = (
                    schedule_key
                )

            # =================================================
            # 🔔 DARS OLDIDAN 10 DAQIQA
            # =================================================

            school_day = (
                python_weekday_to_school_day(
                    now.weekday()
                )
            )

            if school_day is not None:

                schedules = get_schedule(
                    school_day
                )

                for schedule in schedules:

                    start_time = (
                        schedule["start_time"]
                    )

                    try:

                        lesson_start = (
                            datetime.strptime(
                                start_time,
                                "%H:%M"
                            ).time()
                        )

                    except (
                        ValueError,
                        TypeError
                    ):

                        continue

                    lesson_datetime = (
                        datetime.combine(
                            current_date,
                            lesson_start
                        ).replace(
                            tzinfo=UZBEKISTAN_TZ
                        )
                    )

                    reminder_time = (
                        lesson_datetime
                        - timedelta(
                            minutes=10
                        )
                    )

                    reminder_key = (
                        current_date,
                        "lesson",
                        schedule["id"]
                    )

                    if (
                        now.hour
                        == reminder_time.hour
                        and
                        now.minute
                        == reminder_time.minute
                        and
                        reminder_key
                        not in sent_reminders
                    ):

                        await send_lesson_reminder(
                            bot,
                            schedule
                        )

                        sent_reminders.add(
                            reminder_key
                        )

            # =================================================
            # 📝 18:00 — ERTANGI UY VAZIFASI
            # =================================================

            homework_reminder_key = (
                current_date,
                "homework_reminder"
            )

            if (
                current_time == "18:00"
                and
                homework_reminder_key
                not in sent_reminders
            ):

                homework_list = (
                    get_homework()
                )

                tomorrow = (
                    current_date
                    + timedelta(days=1)
                )

                tomorrow_text = (
                    tomorrow.strftime(
                        "%d.%m.%Y"
                    )
                )

                for homework in homework_list:

                    due_date = (
                        homework["due_date"]
                    )

                    if not due_date:
                        continue

                    due_date_text = (
                        str(due_date).strip()
                    )

                    if (
                        due_date_text
                        == tomorrow_text
                    ):

                        await send_homework_reminder(
                            bot,
                            homework
                        )

                sent_reminders.add(
                    homework_reminder_key
                )

            # =================================================
            # 🧹 ESKI KEYLARNI TOZALASH
            # =================================================

            if len(sent_reminders) > 200:

                sent_reminders = {
                    item
                    for item in sent_reminders
                    if item[0] == current_date
                }


        except Exception as error:

            print(
                "❌ Scheduler xatosi:",
                repr(error)
            )

        await asyncio.sleep(
            30
        )

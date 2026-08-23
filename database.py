import sqlite3
import os


# ============================================================
# DATABASE YO'LI
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DB_FILE = os.path.join(DATABASE_DIR, "school.db")


# ============================================================
# DATABASE ULANISH
# ============================================================

def get_connection():
    os.makedirs(DATABASE_DIR, exist_ok=True)

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def get_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row["name"] for row in cursor.fetchall()]


def ensure_column(cursor, table_name, column_name, column_type):
    columns = get_columns(cursor, table_name)

    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )


# ============================================================
# DATABASE INIT / MIGRATION
# ============================================================

def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            class_name TEXT NOT NULL DEFAULT '9-E',
            birth_date TEXT,
            telegram_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "students", "full_name", "TEXT")
    ensure_column(cursor, "students", "class_name", "TEXT DEFAULT '9-E'")
    ensure_column(cursor, "students", "birth_date", "TEXT")
    ensure_column(cursor, "students", "telegram_id", "INTEGER")
    ensure_column(cursor, "students", "created_at", "TEXT")

    # --------------------------------------------------------
    # 👨‍👩‍👦 OTA-ONA HISOBLARI
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parent_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL UNIQUE,
            student_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parent_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    # --------------------------------------------------------
    # O'QUVCHI ULANISH KODLARI
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    # --------------------------------------------------------
    # TEACHERS
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            telegram_id INTEGER UNIQUE,
            subject TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "teachers", "full_name", "TEXT")
    ensure_column(cursor, "teachers", "telegram_id", "INTEGER")
    ensure_column(cursor, "teachers", "subject", "TEXT")
    ensure_column(cursor, "teachers", "is_active", "INTEGER DEFAULT 1")
    ensure_column(cursor, "teachers", "created_at", "TEXT")

    # --------------------------------------------------------
    # SCHEDULES
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER NOT NULL,
            lesson_number INTEGER NOT NULL,
            subject TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(day_of_week, lesson_number)
        )
    """)

    ensure_column(cursor, "schedules", "day_of_week", "INTEGER")
    ensure_column(cursor, "schedules", "lesson_number", "INTEGER")
    ensure_column(cursor, "schedules", "subject", "TEXT")
    ensure_column(cursor, "schedules", "start_time", "TEXT")
    ensure_column(cursor, "schedules", "end_time", "TEXT")
    ensure_column(cursor, "schedules", "created_at", "TEXT")

    # --------------------------------------------------------
    # HOLIDAYS
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            holiday_date TEXT NOT NULL UNIQUE,
            is_day_off INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "holidays", "name", "TEXT")
    ensure_column(cursor, "holidays", "holiday_date", "TEXT")
    ensure_column(cursor, "holidays", "is_day_off", "INTEGER DEFAULT 1")
    ensure_column(cursor, "holidays", "created_at", "TEXT")

    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL,
            lesson_number INTEGER,
            teacher_id INTEGER,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "attendance", "student_id", "INTEGER")
    ensure_column(cursor, "attendance", "attendance_date", "TEXT")
    ensure_column(cursor, "attendance", "status", "TEXT")
    ensure_column(cursor, "attendance", "lesson_number", "INTEGER")
    ensure_column(cursor, "attendance", "teacher_id", "INTEGER")
    ensure_column(cursor, "attendance", "comment", "TEXT")
    ensure_column(cursor, "attendance", "created_at", "TEXT")

    # --------------------------------------------------------
    # GRADES
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            grade INTEGER NOT NULL,
            teacher_id INTEGER,
            grade_date TEXT NOT NULL,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "grades", "student_id", "INTEGER")
    ensure_column(cursor, "grades", "subject", "TEXT")
    ensure_column(cursor, "grades", "grade", "INTEGER")
    ensure_column(cursor, "grades", "teacher_id", "INTEGER")
    ensure_column(cursor, "grades", "grade_date", "TEXT")
    ensure_column(cursor, "grades", "comment", "TEXT")
    ensure_column(cursor, "grades", "created_at", "TEXT")

    # --------------------------------------------------------
    # HOMEWORK
    # --------------------------------------------------------
    # Muhim: eski bazada "description" bor, yangi kodda
    # "homework_text" ishlatiladi. Ikkalasini ham saqlaymiz.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            homework_text TEXT NOT NULL,
            due_date TEXT,
            teacher_id INTEGER,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "homework", "subject", "TEXT")
    ensure_column(cursor, "homework", "homework_text", "TEXT")
    ensure_column(cursor, "homework", "due_date", "TEXT")
    ensure_column(cursor, "homework", "teacher_id", "INTEGER")
    ensure_column(cursor, "homework", "description", "TEXT")
    ensure_column(cursor, "homework", "created_at", "TEXT")

    # Eski yozuvlarda homework_text bo'lmasa description'dan ko'chiramiz.
    cursor.execute("""
        UPDATE homework
        SET homework_text = description
        WHERE (homework_text IS NULL OR homework_text = '')
          AND description IS NOT NULL
    """)

    # --------------------------------------------------------
    # ANNOUNCEMENTS
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            created_by INTEGER,
            is_pinned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "announcements", "title", "TEXT")
    ensure_column(cursor, "announcements", "text", "TEXT")
    ensure_column(cursor, "announcements", "created_by", "INTEGER")
    ensure_column(cursor, "announcements", "is_pinned", "INTEGER DEFAULT 0")
    ensure_column(cursor, "announcements", "created_at", "TEXT")

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            event_time TEXT,
            location TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(cursor, "events", "title", "TEXT")
    ensure_column(cursor, "events", "description", "TEXT")
    ensure_column(cursor, "events", "event_date", "TEXT")
    ensure_column(cursor, "events", "event_time", "TEXT")
    ensure_column(cursor, "events", "location", "TEXT")
    ensure_column(cursor, "events", "created_at", "TEXT")

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    default_settings = {
        "class_name": "9-E",
        "schedule_send_time": "19:00",
        "lesson_reminder_minutes": "10",
        "lesson_duration": "45",
        "group_id": str(PRIMARY_GROUP_ID),
    }

    for key, value in default_settings.items():
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))

    connection.commit()
    connection.close()


# ============================================================
# O'QUVCHILAR
# ============================================================

def add_student(full_name, class_name="9-E", birth_date=None):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO students (
            full_name,
            class_name,
            birth_date
        )
        VALUES (?, ?, ?)
    """, (full_name, class_name, birth_date))

    connection.commit()
    student_id = cursor.lastrowid
    connection.close()

    return student_id


def get_students():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        ORDER BY full_name COLLATE NOCASE
    """)

    result = cursor.fetchall()
    connection.close()
    return result


def get_student(student_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE id = ?
        LIMIT 1
    """, (student_id,))

    result = cursor.fetchone()
    connection.close()
    return result


def search_students(text):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE full_name LIKE ?
        ORDER BY full_name COLLATE NOCASE
    """, (f"%{text}%",))

    result = cursor.fetchall()
    connection.close()
    return result


def clear_students():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM students")

    connection.commit()
    connection.close()


def update_student_birth_date(
    full_name,
    birth_date,
    class_name=None
):
    connection = get_connection()
    cursor = connection.cursor()

    if class_name:
        cursor.execute("""
            UPDATE students
            SET birth_date = ?,
                class_name = ?
            WHERE full_name = ?
        """, (birth_date, class_name, full_name))
    else:
        cursor.execute("""
            UPDATE students
            SET birth_date = ?
            WHERE full_name = ?
        """, (birth_date, full_name))

    connection.commit()
    connection.close()





# ============================================================
# 👨‍🎓 O'QUVCHI TELEGRAM ULANISH
# ============================================================

def get_student_by_telegram_id(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE telegram_id = ?
        LIMIT 1
    """, (telegram_id,))

    result = cursor.fetchone()
    connection.close()
    return result


def create_student_code(student_id, hours=24):
    import random
    from datetime import datetime, timedelta

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM students WHERE id = ? LIMIT 1",
        (student_id,)
    )

    if not cursor.fetchone():
        connection.close()
        return None

    code = None

    for _ in range(30):
        candidate = str(random.randint(100000, 999999))

        cursor.execute(
            "SELECT id FROM student_codes WHERE code = ? LIMIT 1",
            (candidate,)
        )

        if not cursor.fetchone():
            code = candidate
            break

    if code is None:
        connection.close()
        raise RuntimeError("O'quvchi kodi yaratilmadi.")

    expires_at = (
        datetime.now() + timedelta(hours=hours)
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "DELETE FROM student_codes WHERE student_id = ?",
        (student_id,)
    )

    cursor.execute("""
        INSERT INTO student_codes (
            student_id, code, expires_at
        )
        VALUES (?, ?, ?)
    """, (student_id, code, expires_at))

    connection.commit()
    connection.close()
    return code


def link_student_by_code(telegram_id, code):
    from datetime import datetime

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, student_id, expires_at
        FROM student_codes
        WHERE code = ?
        LIMIT 1
    """, (str(code).strip(),))

    row = cursor.fetchone()

    if not row:
        connection.close()
        return None

    try:
        expired = (
            datetime.now()
            > datetime.strptime(
                row["expires_at"],
                "%Y-%m-%d %H:%M:%S"
            )
        )
    except (ValueError, TypeError):
        expired = True

    if expired:
        cursor.execute(
            "DELETE FROM student_codes WHERE id = ?",
            (row["id"],)
        )
        connection.commit()
        connection.close()
        return None

    # Bitta Telegram akkaunti bir vaqtning o'zida
    # faqat bitta o'quvchiga bog'lanadi.
    cursor.execute("""
        UPDATE students
        SET telegram_id = NULL
        WHERE telegram_id = ?
          AND id != ?
    """, (telegram_id, row["student_id"]))

    cursor.execute("""
        UPDATE students
        SET telegram_id = ?
        WHERE id = ?
    """, (telegram_id, row["student_id"]))

    if cursor.rowcount == 0:
        connection.close()
        return None

    cursor.execute(
        "DELETE FROM student_codes WHERE id = ?",
        (row["id"],)
    )

    connection.commit()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE id = ?
        LIMIT 1
    """, (row["student_id"],))

    student = cursor.fetchone()
    connection.close()
    return student


# ============================================================
# 👨‍👩‍👦 OTA-ONA TIZIMI
# ============================================================

def create_parent_code(student_id, hours=24):
    """
    Ota-ona uchun bir martalik 6 xonali ulanish kodi yaratadi.
    Kod 24 soat amal qiladi.
    """
    import random
    from datetime import datetime, timedelta

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM students WHERE id = ? LIMIT 1",
        (student_id,)
    )

    if not cursor.fetchone():
        connection.close()
        return None

    code = None

    for _ in range(20):
        candidate = str(
            random.randint(100000, 999999)
        )

        cursor.execute(
            "SELECT id FROM parent_codes WHERE code = ? LIMIT 1",
            (candidate,)
        )

        if not cursor.fetchone():
            code = candidate
            break

    if code is None:
        connection.close()
        raise RuntimeError("Ulanish kodi yaratilmadi.")

    expires_at = (
        datetime.now() + timedelta(hours=hours)
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "DELETE FROM parent_codes WHERE student_id = ?",
        (student_id,)
    )

    cursor.execute("""
        INSERT INTO parent_codes (
            student_id,
            code,
            expires_at
        )
        VALUES (?, ?, ?)
    """, (
        student_id,
        code,
        expires_at
    ))

    connection.commit()
    connection.close()

    return code


def link_parent_by_code(telegram_id, code):
    """
    Ota-ona kodni kiritganda Telegram hisobini o'quvchiga bog'laydi.
    Natija: student row yoki None.
    """
    from datetime import datetime

    code = str(code).strip()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            student_id,
            expires_at
        FROM parent_codes
        WHERE code = ?
        LIMIT 1
    """, (code,))

    row = cursor.fetchone()

    if not row:
        connection.close()
        return None

    try:
        expired = (
            datetime.now()
            > datetime.strptime(
                row["expires_at"],
                "%Y-%m-%d %H:%M:%S"
            )
        )
    except ValueError:
        expired = True

    if expired:
        cursor.execute(
            "DELETE FROM parent_codes WHERE id = ?",
            (row["id"],)
        )
        connection.commit()
        connection.close()
        return None

    cursor.execute("""
        INSERT INTO parent_accounts (
            telegram_id,
            student_id
        )
        VALUES (?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET
            student_id = excluded.student_id
    """, (
        telegram_id,
        row["student_id"]
    ))

    cursor.execute(
        "DELETE FROM parent_codes WHERE id = ?",
        (row["id"],)
    )

    connection.commit()

    cursor.execute("""
        SELECT *
        FROM students
        WHERE id = ?
        LIMIT 1
    """, (row["student_id"],))

    student = cursor.fetchone()

    connection.close()

    return student


def get_parent_student(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT students.*
        FROM parent_accounts
        JOIN students
            ON students.id = parent_accounts.student_id
        WHERE parent_accounts.telegram_id = ?
        LIMIT 1
    """, (telegram_id,))

    result = cursor.fetchone()

    connection.close()

    return result


def unlink_parent(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM parent_accounts WHERE telegram_id = ?",
        (telegram_id,)
    )

    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted


def get_parent_accounts():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            parent_accounts.telegram_id,
            parent_accounts.created_at,
            students.id AS student_id,
            students.full_name,
            students.class_name
        FROM parent_accounts
        JOIN students
            ON students.id = parent_accounts.student_id
        ORDER BY students.full_name COLLATE NOCASE
    """)

    result = cursor.fetchall()

    connection.close()

    return result


# ============================================================
# O'QITUVCHILAR
# ============================================================

def add_teacher(full_name, telegram_id, subject=None):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM teachers
        WHERE telegram_id = ?
        LIMIT 1
    """, (telegram_id,))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE teachers
            SET full_name = ?,
                subject = ?,
                is_active = 1
            WHERE id = ?
        """, (full_name, subject, existing["id"]))
    else:
        cursor.execute("""
            INSERT INTO teachers (
                full_name,
                telegram_id,
                subject,
                is_active
            )
            VALUES (?, ?, ?, 1)
        """, (full_name, telegram_id, subject))

    connection.commit()
    connection.close()


def get_teachers():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE COALESCE(is_active, 1) = 1
        ORDER BY full_name COLLATE NOCASE
    """)

    result = cursor.fetchall()
    connection.close()
    return result


def get_teacher_by_telegram_id(telegram_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE telegram_id = ?
          AND COALESCE(is_active, 1) = 1
        LIMIT 1
    """, (telegram_id,))

    result = cursor.fetchone()
    connection.close()
    return result


def delete_teacher(teacher_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE teachers
        SET is_active = 0
        WHERE id = ?
    """, (teacher_id,))

    connection.commit()
    connection.close()


# ============================================================
# DARS JADVALI
# ============================================================

def add_schedule(
    day_of_week,
    lesson_number,
    subject,
    start_time,
    end_time
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM schedules
        WHERE day_of_week = ?
          AND lesson_number = ?
        LIMIT 1
    """, (day_of_week, lesson_number))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE schedules
            SET subject = ?,
                start_time = ?,
                end_time = ?
            WHERE id = ?
        """, (
            subject,
            start_time,
            end_time,
            existing["id"],
        ))
    else:
        cursor.execute("""
            INSERT INTO schedules (
                day_of_week,
                lesson_number,
                subject,
                start_time,
                end_time
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            day_of_week,
            lesson_number,
            subject,
            start_time,
            end_time,
        ))

    connection.commit()
    connection.close()


def get_schedule(day_of_week):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM schedules
        WHERE day_of_week = ?
        ORDER BY lesson_number
    """, (day_of_week,))

    result = cursor.fetchall()
    connection.close()
    return result


def get_all_schedules():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM schedules
        ORDER BY day_of_week, lesson_number
    """)

    result = cursor.fetchall()
    connection.close()
    return result


def delete_schedule(day_of_week, lesson_number):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM schedules
        WHERE day_of_week = ?
          AND lesson_number = ?
    """, (day_of_week, lesson_number))

    connection.commit()
    connection.close()


# ============================================================
# BAYRAMLAR
# ============================================================

def add_holiday(name, holiday_date, is_day_off=1):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM holidays
        WHERE holiday_date = ?
        LIMIT 1
    """, (holiday_date,))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE holidays
            SET name = ?,
                is_day_off = ?
            WHERE id = ?
        """, (name, is_day_off, existing["id"]))
    else:
        cursor.execute("""
            INSERT INTO holidays (
                name,
                holiday_date,
                is_day_off
            )
            VALUES (?, ?, ?)
        """, (name, holiday_date, is_day_off))

    connection.commit()
    connection.close()


def get_holiday(holiday_date):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM holidays
        WHERE holiday_date = ?
        LIMIT 1
    """, (holiday_date,))

    result = cursor.fetchone()
    connection.close()
    return result


def get_holidays():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM holidays
        ORDER BY holiday_date
    """)

    result = cursor.fetchall()
    connection.close()
    return result


def delete_holiday(holiday_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM holidays
        WHERE id = ?
    """, (holiday_id,))

    connection.commit()
    connection.close()


def is_day_off(holiday_date):
    holiday = get_holiday(holiday_date)

    if holiday:
        return bool(holiday["is_day_off"])

    return False


# ============================================================
# DAVOMAT
# ============================================================

def add_attendance(
    student_id,
    attendance_date,
    status,
    lesson_number=None,
    teacher_id=None,
    comment=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM attendance
        WHERE student_id = ?
          AND attendance_date = ?
          AND COALESCE(lesson_number, 0) =
              COALESCE(?, 0)
        LIMIT 1
    """, (
        student_id,
        attendance_date,
        lesson_number,
    ))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE attendance
            SET status = ?,
                teacher_id = ?,
                comment = ?
            WHERE id = ?
        """, (
            status,
            teacher_id,
            comment,
            existing["id"],
        ))
    else:
        cursor.execute("""
            INSERT INTO attendance (
                student_id,
                attendance_date,
                status,
                lesson_number,
                teacher_id,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            attendance_date,
            status,
            lesson_number,
            teacher_id,
            comment,
        ))

    connection.commit()
    connection.close()


def get_student_attendance(student_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM attendance
        WHERE student_id = ?
        ORDER BY attendance_date DESC,
                 lesson_number
    """, (student_id,))

    result = cursor.fetchall()
    connection.close()
    return result


def get_attendance_by_date(attendance_date):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            attendance.*,
            students.full_name
        FROM attendance
        JOIN students
          ON students.id = attendance.student_id
        WHERE attendance.attendance_date = ?
        ORDER BY students.full_name
    """, (attendance_date,))

    result = cursor.fetchall()
    connection.close()
    return result


def get_attendance_for_lesson(
    attendance_date,
    lesson_number
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            attendance.*,
            students.full_name
        FROM attendance
        JOIN students
          ON students.id = attendance.student_id
        WHERE attendance.attendance_date = ?
          AND attendance.lesson_number = ?
        ORDER BY students.full_name
    """, (attendance_date, lesson_number))

    result = cursor.fetchall()
    connection.close()
    return result


# ============================================================
# BAHOLAR
# ============================================================

def add_grade(
    student_id,
    subject,
    grade,
    teacher_id=None,
    grade_date=None,
    comment=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO grades (
            student_id,
            subject,
            grade,
            teacher_id,
            grade_date,
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        subject,
        grade,
        teacher_id,
        grade_date,
        comment,
    ))

    connection.commit()
    connection.close()


def get_student_grades(student_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM grades
        WHERE student_id = ?
        ORDER BY grade_date DESC, id DESC
    """, (student_id,))

    result = cursor.fetchall()
    connection.close()
    return result


# ============================================================
# UY VAZIFALARI
# ============================================================

def add_homework(
    subject,
    homework_text,
    due_date=None,
    teacher_id=None
):
    connection = get_connection()
    cursor = connection.cursor()

    # description eski database versiyasi uchun ham
    # to'ldiriladi.
    cursor.execute("""
        INSERT INTO homework (
            subject,
            homework_text,
            due_date,
            teacher_id,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        subject,
        homework_text,
        due_date,
        teacher_id,
        homework_text,
    ))

    connection.commit()
    homework_id = cursor.lastrowid
    connection.close()

    return homework_id


def get_homework():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            subject,
            COALESCE(
                NULLIF(homework_text, ''),
                description
            ) AS homework_text,
            due_date,
            teacher_id,
            created_at,
            description
        FROM homework
        ORDER BY
            CASE
                WHEN due_date IS NULL OR due_date = ''
                THEN 1
                ELSE 0
            END,
            due_date,
            created_at DESC
    """)

    result = cursor.fetchall()
    connection.close()
    return result


def get_homework_by_id(homework_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            subject,
            COALESCE(
                NULLIF(homework_text, ''),
                description
            ) AS homework_text,
            due_date,
            teacher_id,
            created_at,
            description
        FROM homework
        WHERE id = ?
        LIMIT 1
    """, (homework_id,))

    result = cursor.fetchone()
    connection.close()
    return result


def delete_homework(homework_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM homework
        WHERE id = ?
    """, (homework_id,))

    connection.commit()
    deleted = cursor.rowcount
    connection.close()

    return deleted > 0


# ============================================================
# E'LONLAR
# ============================================================

def add_announcement(
    title,
    text,
    created_by=None,
    is_pinned=0
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO announcements (
            title,
            text,
            created_by,
            is_pinned
        )
        VALUES (?, ?, ?, ?)
    """, (
        title,
        text,
        created_by,
        is_pinned,
    ))

    connection.commit()
    announcement_id = cursor.lastrowid
    connection.close()

    return announcement_id


def get_announcements():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM announcements
        ORDER BY
            COALESCE(is_pinned, 0) DESC,
            created_at DESC,
            id DESC
    """)

    result = cursor.fetchall()
    connection.close()
    return result


def delete_announcement(announcement_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM announcements
        WHERE id = ?
    """, (announcement_id,))

    connection.commit()
    deleted = cursor.rowcount
    connection.close()

    return deleted > 0


# ============================================================
# TADBIRLAR
# ============================================================

def add_event(
    title,
    description,
    event_date,
    event_time=None,
    location=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO events (
            title,
            description,
            event_date,
            event_time,
            location
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        title,
        description,
        event_date,
        event_time,
        location,
    ))

    connection.commit()
    event_id = cursor.lastrowid
    connection.close()

    return event_id


def get_events():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM events
        ORDER BY event_date, event_time, id
    """)

    result = cursor.fetchall()
    connection.close()
    return result


def delete_event(event_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM events
        WHERE id = ?
    """, (event_id,))

    connection.commit()
    deleted = cursor.rowcount
    connection.close()

    return deleted > 0


# ============================================================
# SETTINGS
# ============================================================

def set_setting(key, value):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (key, str(value)))

    connection.commit()
    connection.close()


def get_setting(key, default=None):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT value
        FROM settings
        WHERE key = ?
        LIMIT 1
    """, (key,))

    result = cursor.fetchone()
    connection.close()

    if result:
        return result["value"]

    return default


# ============================================================
# GROUP ID — 9-E ASOSIY GURUH
# ============================================================

# 9-E sinfning yagona rasmiy Telegram guruhi.
# Barcha e'lon, jadval, uy vazifasi va avtomatik
# eslatmalar shu guruhga yuboriladi.
PRIMARY_GROUP_ID = int(
    os.getenv("PRIMARY_GROUP_ID", "-1001645309356").strip()
)


def set_group_id(group_id):
    """
    Faqat 9-E guruhini asosiy guruh sifatida qabul qiladi.
    """
    group_id = int(group_id)

    if group_id != PRIMARY_GROUP_ID:
        raise ValueError(
            f"Bu bot faqat 9-E guruhiga ulangan. "
            f"Ruxsat etilgan ID: {PRIMARY_GROUP_ID}"
        )

    # Database'ga ham yozamiz.
    set_setting("group_id", str(PRIMARY_GROUP_ID))
    return str(PRIMARY_GROUP_ID)


def get_group_id():
    """
    9-E uchun yagona group ID.
    Database bo'sh bo'lsa ham PRIMARY_GROUP_ID qaytariladi.
    """
    return str(PRIMARY_GROUP_ID)


# ============================================================
# GROUP ID STARTUP VERIFICATION
# ============================================================

# init_database() vaqtida settings.group_id bo'sh bo'lsa ham,
# uni 9-E ning rasmiy ID'siga to'ldiramiz.
try:
    init_database()
    set_setting("group_id", str(PRIMARY_GROUP_ID))
except Exception as exc:
    print(f"⚠️ GROUP ID INIT ERROR: {exc}")


# ============================================================
# DATABASE TEST
# ============================================================

if __name__ == "__main__":
    init_database()

    connection = get_connection()
    cursor = connection.cursor()

    print()
    print("========================================")
    print("          9-E SCHOOL DATABASE")
    print("========================================")
    print()
    print("📁 Database:")
    print(os.path.abspath(DB_FILE))
    print()

    students = get_students()
    teachers = get_teachers()
    homework = get_homework()

    print(f"👥 O'quvchilar: {len(students)} ta")
    print(f"👨‍🏫 O'qituvchilar: {len(teachers)} ta")
    print(f"📝 Uy vazifalari: {len(homework)} ta")
    print()
    print("✅ Database tayyor!")

    connection.close()

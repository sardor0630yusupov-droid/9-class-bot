from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👥 O‘quvchilar"),
            KeyboardButton(text="👨‍🏫 O‘qituvchilar")
        ],
        [
            KeyboardButton(text="📅 Dars jadvali"),
            KeyboardButton(text="📝 Uy vazifalari")
        ],
        [
            KeyboardButton(text="📊 Davomat"),
            KeyboardButton(text="⭐ Baholar")
        ],
        [
            KeyboardButton(text="🏆 Reyting"),
            KeyboardButton(text="📢 E'lonlar")
        ],
        [
            KeyboardButton(text="🎉 Bayramlar"),
            KeyboardButton(text="🎂 Tug‘ilgan kunlar")
        ],
        [
            KeyboardButton(text="📸 Tadbirlar"),
            KeyboardButton(text="⚙️ Sozlamalar")
        ]
    ],
    resize_keyboard=True,
    is_persistent=True
)
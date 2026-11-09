import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL = os.getenv("CHANNEL", "@UzPayShoop")
DB_PATH = os.getenv("DB_PATH", "orders.db")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "").strip().lstrip("@")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida kiritilmagan.")
if ADMIN_ID <= 0:
    raise RuntimeError("ADMIN_ID .env faylida to'g'ri kiritilmagan.")

logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

CATALOG = {
    "stars": ("⭐ Telegram Stars", "Telegram Stars buyurtmasi"),
    "premium": ("💎 Telegram Premium", "Telegram Premium buyurtmasi"),
    "gifts": ("🎁 Telegram Gifts", "Telegram Gifts buyurtmasi"),
    "numbers": ("📱 Virtual raqamlar", "Virtual raqam buyurtmasi"),
}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            category TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Yangi',
            created_at TEXT NOT NULL
        )
        """)

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Stars", callback_data="cat:stars"),
         InlineKeyboardButton(text="💎 Premium", callback_data="cat:premium")],
        [InlineKeyboardButton(text="🎁 Gifts", callback_data="cat:gifts"),
         InlineKeyboardButton(text="📱 Virtual raqamlar", callback_data="cat:numbers")],
        [InlineKeyboardButton(text="📦 Buyurtmalarim", callback_data="myorders")],
        [InlineKeyboardButton(text="💳 To'lov usullari", callback_data="payments"),
         InlineKeyboardButton(text="☎️ Yordam", callback_data="support")],
    ])

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🛍 <b>UzPayShoop</b> xizmatlar do'koniga xush kelibsiz!\n\n"
        "Kerakli xizmatni tanlang. Buyurtmangiz admin tomonidan tasdiqlanadi.",
        reply_markup=main_menu()
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("Buyurtma berish uchun menyudan xizmatni tanlang.", reply_markup=main_menu())

@dp.callback_query(F.data == "home")
async def home(call: CallbackQuery):
    await call.message.edit_text("🛍 <b>UzPayShoop</b>\nKerakli bo'limni tanlang:", reply_markup=main_menu())
    await call.answer()

@dp.callback_query(F.data.startswith("cat:"))
async def category(call: CallbackQuery):
    key = call.data.split(":", 1)[1]
    title, description = CATALOG[key]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Buyurtma berish", callback_data=f"order:{key}")],
        [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")]
    ])
    await call.message.edit_text(
        f"<b>{title}</b>\n{description}.\n\n"
        "Buyurtma berish tugmasini bosing. Keyingi xabarda kerakli miqdor yoki tafsilotni yozing.",
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query(F.data.startswith("order:"))
async def order_start(call: CallbackQuery):
    key = call.data.split(":", 1)[1]
    title = CATALOG[key][0]
    await call.message.answer(
        f"📝 <b>{title}</b>\n\n"
        "Buyurtma tafsilotini bitta xabarda yuboring.\n"
        "Masalan: <code>100 Stars, akkaunt: @username</code>\n\n"
        "Shaxsiy parol yoki SMS tasdiqlash kodini yubormang."
    )
    # One-shot pending state kept in memory; order is persisted once submitted.
    pending[call.from_user.id] = key
    await call.answer()

pending = {}

@dp.message(F.text)
async def receive_order(message: Message):
    user_id = message.from_user.id
    if user_id not in pending:
        return
    key = pending.pop(user_id)
    details = message.text.strip()
    if len(details) < 3 or len(details) > 1000:
        await message.answer("Tafsilot 3–1000 belgi oralig'ida bo'lishi kerak. Qayta yuboring.")
        pending[user_id] = key
        return
    username = message.from_user.username or ""
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO orders(user_id, username, category, details, status, created_at) VALUES(?,?,?,?,?,?)",
            (user_id, username, key, details, "Yangi", datetime.utcnow().isoformat(timespec="seconds"))
        )
        order_id = cur.lastrowid
    title = CATALOG[key][0]
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"status:{order_id}:Tasdiqlandi"),
         InlineKeyboardButton(text="❌ Rad etish", callback_data=f"status:{order_id}:Rad etildi")],
        [InlineKeyboardButton(text="💰 To'landi", callback_data=f"status:{order_id}:To'landi")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"🆕 <b>Yangi buyurtma #{order_id}</b>\n"
        f"Xizmat: {title}\nFoydalanuvchi: {message.from_user.full_name} "
        f"(@{username or 'username yo‘q'})\nID: <code>{user_id}</code>\n"
        f"Tafsilot: {details}",
        reply_markup=admin_kb
    )
    await message.answer(
        f"✅ Buyurtmangiz qabul qilindi! <b>#{order_id}</b>\n"
        "Admin tekshirganidan keyin holati haqida xabar olasiz.",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data.startswith("status:"))
async def update_status(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Bu amal faqat admin uchun.", show_alert=True)
        return
    _, raw_id, status = call.data.split(":", 2)
    order_id = int(raw_id)
    with db() as conn:
        row = conn.execute("SELECT user_id FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            await call.answer("Buyurtma topilmadi.", show_alert=True)
            return
        conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    await bot.send_message(row["user_id"], f"📦 <b>#{order_id}</b> buyurtmangiz holati: <b>{status}</b>.")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("Holat yangilandi.")

@dp.callback_query(F.data == "myorders")
async def my_orders(call: CallbackQuery):
    with db() as conn:
        rows = conn.execute(
            "SELECT id, category, details, status, created_at FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",
            (call.from_user.id,)
        ).fetchall()
    if not rows:
        text = "Sizda hozircha buyurtmalar yo'q."
    else:
        text = "<b>📦 Oxirgi buyurtmalaringiz</b>\n\n"
        for r in rows:
            text += f"#{r['id']} · {CATALOG[r['category']][0]}\nHolat: <b>{r['status']}</b>\n{r['details']}\n\n"
    await call.message.edit_text(text, reply_markup=back_menu())
    await call.answer()

@dp.callback_query(F.data == "payments")
async def payments(call: CallbackQuery):
    await call.message.edit_text(
        "💳 <b>To'lov usullari</b>\n\n"
        "Click / Payme / Uzum Bank bo'yicha to'lov rekvizitlari admin tomonidan buyurtma tasdiqlangach yuboriladi.\n"
        "Hozircha bot ichida avtomatik karta yechimi yoki to'lov tasdig'i yo'q. To'lovni faqat admin yuborgan rasmiy rekvizit orqali amalga oshiring.",
        reply_markup=back_menu()
    )
    await call.answer()

@dp.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    if SUPPORT_USERNAME:
        text = f"☎️ Yordam: @{SUPPORT_USERNAME}"
    else:
        text = "☎️ Yordam uchun bot administratoriga murojaat qiling."
    await call.message.edit_text(text, reply_markup=back_menu())
    await call.answer()

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) n FROM orders").fetchone()["n"]
        fresh = conn.execute("SELECT COUNT(*) n FROM orders WHERE status='Yangi'").fetchone()["n"]
    await message.answer(f"👨‍💻 <b>Admin panel</b>\nJami buyurtmalar: {total}\nYangi: {fresh}")

async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("UzPayShoop bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

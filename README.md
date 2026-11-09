# UzPayShoop Telegram bot

## Hozir ishlaydigan funksiyalar
- Uzbekcha menyu: Stars, Premium, Gifts, virtual raqamlar.
- Foydalanuvchi buyurtma yuboradi.
- Buyurtmalar SQLite bazasiga yoziladi.
- Admin yangi buyurtmani oladi va tasdiqlaydi/rad etadi/to'landi deb belgilaydi.
- Foydalanuvchi buyurtma holati va oxirgi 10 ta buyurtmasini ko'radi.

## Muhim
Click, Payme va Uzum Bank avtomatik to'lov API'lari bu starter loyihaga ulanmagan. Bot hozircha to'lov rekvizitlarini admin orqali yuborish uchun tayyorlangan; haqiqiy avtomatik to'lov uchun merchant API kalitlari va tasdiqlangan merchant akkauntlari kerak. Telegram Stars invoice ham mahsulot narxlari aniq belgilanmagani sababli hozircha yoqilmagan.

## Ishga tushirish
1. Python 3.10+ o'rnating.
2. `pip install -r requirements.txt`
3. `.env.example` faylini `.env` deb nomlang.
4. `BOT_TOKEN` va `ADMIN_ID` ni kiriting.
5. `python bot.py`

## Render
GitHub'ga loyihani yuklang, Render'da New > Blueprint tanlang va repo'ni ulang. Render Environment'da BOT_TOKEN va ADMIN_ID ni kiriting. `render.yaml` worker servisni yaratadi.

## Xavfsizlik
- Bot tokenini hech kimga yubormang yoki GitHub'ga commit qilmang.
- Foydalanuvchilardan Telegram paroli yoki SMS kod so'ramang.
- SQLite fayli Render ephemeral diskida saqlanadi; doimiy buyurtma tarixi uchun Render persistent disk yoki tashqi PostgreSQL kerak.

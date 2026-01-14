import asyncio
import re
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.error import TelegramError
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, ContextTypes, filters
)

# ===== CONFIG =====
# Bot tokeningizni kiriting
TOKEN = "8528647202:AAHrcOe4Zg6lAaxQweqxiVqljXMuqsD6da8"

# ===== States =====
TIL, MINTQA, MENU, BOLM, LINK, MATN, VAQT, TAKROR, OLDINDAN, TAHRIR, EXIT_EDIT = range(11)

# ===== Database (Memory) =====
users = {}
tasks = {}

# ===== Static Data =====
ZONE_MAP = {
    # 🇺🇿 Toshkent
    "toshkent": "Asia/Tashkent",
    "ташкент": "Asia/Tashkent",
    "uzbekistan": "Asia/Tashkent",
    "узбекистан": "Asia/Tashkent",

    # 🇷🇺 Rossiya (Moskva vaqti)
    "rossiya": "Europe/Moscow",
    "russia": "Europe/Moscow",
    "россия": "Europe/Moscow",
    "moskva": "Europe/Moscow",
    "москва": "Europe/Moscow",

    # 🇺🇸 New York
    "new york": "America/New_York",
    "newyork": "America/New_York",
    "ny": "America/New_York",
    "нью-йорк": "America/New_York",
    "niyork": "America/New_York"
}



STRINGS = {
    "UZ": {
        "start": "🌐 Tilni tanlang:",
        "ask_tz": "🗺 Mintaqangizni kiriting (masalan: Toshkent, Moskva):",
        "menu": "📌 Asosiy menyu! Kerakli bo‘limni tanlang 👇\n\n➕ Eslatma qo‘shish — yangi eslatma yarating va vaqtini belgilang\n\n📋 Eslatmalar ro‘yxati — barcha eslatmalarni ko‘rish va tahrirlash\n\n📖 Qo‘llanma va yordam — botdan foydalanish bo‘yicha yo‘riqnoma",
        "btn_new": "➕ Yangi eslatma",
        "btn_list": "📋 Ro‘yxat (Bo'limlar)",
        "btn_back": "⬅️ Orqaga",
        "ask_bolm": "🔔 Eslatma turini tanlang!\n\nIltimos, quyidagi variantlardan birini tanlang:\n\n👤 Shaxsiy — eslatma faqat sizga keladi\n\n👥 Guruh — eslatma guruhlarda keladi\n\n📢 Kanal — eslatma kanallarda keladi",
        "ask_link": "🔗 {} uchun ID yoki Linkni kiriting:\n\n⚠️ DIQQAT: Botni kanal/guruhga ADMIN qiling, aks holda xabar yubora olmaydi!",
        "ask_text": "📝 Eslatma matnini kiriting.\n\nMasalan:\nHisobotni topshirish;\nDo'stimning tug'ilgan kuni bilan tabriklash;\nHar 3 oyda tish schetkalarni almashtirish;\nva hokazo...",
        "ask_time": "⏰ Vaqtni kiriting (Masalan: 15.01.2026 14:00):",
       "ask_rep": "🔁 Eslatma takrorlansinmi?\n\nMasalan:\nHar kuni\nHar hafta\nHar oy\nva hokazo...",
        "ask_pre": "⏰ Oldindan eslatilsinmi?\n\nMasalan:\n5 daqiqa oldin\n1 soat oldin\n1 kun oldin\nva hokazo...\n\n1 d = 1 daqiqa\n1 s = 1 soat\n1 k = 1 kun",
        "error_tz": "⚠️ Mintaqa topilmadi, Toshkent vaqti o'rnatildi.",
        "error_time": "❌ Vaqt o'tmishda yoki noto'g'ri!",
        "success": "✅ Eslatma muvaffaqiyatli o'rnatildi!",
        "no_rem": "📭 Bu bo'limda eslatmalar yo'q.",
        "btn_edit_text": "📝 Matn",
        "btn_edit_time": "⏰ Vaqt",
        "btn_edit_rep": "🔁 Takrorlash",
        "btn_edit_pre": "🔔 Oldindan",
        "btn_toggle": "🚫 Yoqish/O'chirish",
        "btn_del": "🗑 O'chirish",
        "status_on": "✅ Yoqilgan",
        "status_off": "💤 O'chirilgan",
        "btn_personal": "👤 Shaxsiy",
        "btn_group": "👥 Guruh",
        "btn_channel": "📢 Kanal",
        "ask_list_bolm": "📋 Eslatmalar ro‘yxati!\n\nKerakli bo‘limni tanlang 👇",  
        "section": "Bo'lim",
        "location": "Manzil",
        "text": "Matn",
        "time": "Vaqt",
        "repeat": "Takror",
        "pre_rem": "Oldindan",
        "status": "Holat"
    },
    "RU": {
        "start": "🌐 Выберите язык:",
        "ask_tz": "🗺 Введите ваш регион (например: Ташкент, Москва):",
        "menu": "📌 Главное меню! Выберите нужный раздел 👇\n\n➕ Добавить напоминание — создайте новое напоминание и укажите время\n\n📋 Список напоминаний — просмотр и редактирование всех напоминаний\n\n📖 Инструкция и помощь — руководство по использованию бота",
        "btn_new": "➕ Новое напоминание",
        "btn_list": "📋 Список (Разделы)",
        "btn_back": "⬅️ Назад",
        "ask_bolm": "🔔 Выберите тип напоминания!\n\nПожалуйста, выберите один из вариантов:\n\n👤 Личное — напоминание придёт только вам\n\n👥 Группа — напоминание придёт в группах\n\n📢 Канал — напоминание придёт в каналах",
        "ask_link": "🔗 Введите ID или ссылку для {}:\n\n⚠️ ВНИМАНИЕ: Сделайте бота АДМИНИСТРАТОРОМ в группе/канале, иначе он не сможет отправлять сообщения!",
        "ask_text": "📝 Введите текст напоминания.\n\nНапример:\nСдать отчёт;\nПоздравить друга с днём рождения;\nМенять зубные щётки каждые 3 месяца;\nи так далее...",
        "ask_time": "⏰ Введите время (например: 15.01.2026 14:00):",
        "ask_rep": "🔁 Повторять напоминание?\n\nНапример:\nКаждый день\nКаждую неделю\nКаждый месяц\nи так далее...",
        "ask_pre": "⏰ Напомнить заранее?\n\nНапример:\nза 5 минут\nза 1 час\nза 1 день\nи так далее...\n\n1 м = 1 минута\n1 ч = 1 час\n1 д = 1 день",
        "error_tz": "⚠️ Регион не найден, установлено время Ташкента.",
        "error_time": "❌ Время указано неверно или находится в прошлом!",
        "success": "✅ Напоминание успешно установлено!",
        "no_rem": "📭 В этом разделе нет напоминаний.",
        "btn_edit_text": "📝 Текст",
        "btn_edit_time": "⏰ Время",
        "btn_edit_rep": "🔁 Повтор",
        "btn_edit_pre": "🔔 Заранее",
        "btn_toggle": "🚫 Включить/Выключить",
        "btn_del": "🗑 Удалить",
        "status_on": "✅ Включено",
        "status_off": "💤 Выключено",
        "btn_personal": "👤 Личное",
        "btn_group": "👥 Группа",
        "btn_channel": "📢 Канал",
        "ask_list_bolm": "📋 Список напоминаний!\n\nВыберите нужный раздел 👇",
        "section": "Раздел",
        "location": "Место",
        "text": "Текст",
        "time": "Время",
        "repeat": "Повтор",
        "pre_rem": "Заранее",
        "status": "Статус"
    }
}

# ===== Keyboards =====
def get_rep_kb(uid):
    lang = users.get(uid, {}).get("lang", "UZ")
    if lang == "UZ":
        return [
            ["❌ Hech qachon", "🔄 Har kuni"],
            ["📅 Har hafta", "🗓 Har 2 haftada"],
            ["Har oy", "3 oyda"],
            ["6 oyda", "Har yili"],
            ["✍️ Qo'lda"]
        ]
    else:  # RU
        return [
            ["❌ Никогда", "🔄 Каждый день"],
            ["📅 Каждую неделю", "🗓 Каждые 2 недели"],
            ["Каждый месяц", "Каждые 3 месяца"],
            ["Каждые 6 месяцев", "Каждый год"],
            ["✍️ Вручную"]
        ]

def get_pre_kb(uid):
    lang = users.get(uid, {}).get("lang", "UZ")
    if lang == "UZ":
        return [
            ["❌ Yo'q", "1 daqiqa", "5 daqiqa"],
            ["10 daqiqa", "30 daqiqa", "1 soat"],
            ["3 soat", "6 soat", "12 soat"],
            ["1 kun", "2 kun", "✍️ Qo'lda"]
        ]
    else:  # RU
        return [
            ["❌ Нет", "1 минута", "5 минут"],
            ["10 минут", "30 минут", "1 час"],
            ["3 часа", "6 часов", "12 часов"],
            ["1 день", "2 дня", "✍️ Вручную"]
        ]


# ===== Helpers =====
def get_s(uid, key):
    lang = users.get(uid, {}).get("lang", "UZ")
    return STRINGS[lang].get(key, key)

def parse_duration(text):
    text = text.lower().strip()
    match = re.search(r"(\d+)", text)
    if not match: return None
    val = int(match.group(1))
    if any(x in text for x in ["kun", "день", "d"]): return timedelta(days=val)
    if any(x in text for x in ["soat", "час", "h", "s"]): return timedelta(hours=val)
    if any(x in text for x in ["daqiqa", "мин", "m", "d"]): return timedelta(minutes=val)
    if any(x in text for x in ["hafta", "недел", "w"]): return timedelta(weeks=val)
    return None

def format_reminder_text(uid, r):
    s = STRINGS[users[uid]["lang"]]
    status = s["status_on"] if r.get("is_active") else s["status_off"]
    rep = "Yo'q" if not r.get('repeat') else f"{r['repeat']}"
    pre = f"{r.get('pre_rem', 0)} min oldin"
    
    return (f"{s['section']}: {r['bolm']}\n"
            f"{s['location']}: {r.get('link', s['btn_personal'])}\n"
            f"{s['text']}: {r['text']}\n"
            f"{s['time']}: {r['time'].strftime('%d.%m.%Y %H:%M')}\n"
            f"{s['repeat']}: {rep}\n"
            f"{s['pre_rem']}: {pre}\n"
            f"{s['status']}: {status}")


# ===== CORE FUNCTIONS =====
async def send_reminder(context, target, message):
    """Xabar yuborish funksiyasi - xatoliklarni tekshiradi"""
    try:
        await context.bot.send_message(chat_id=target, text=message)
        return True
    except TelegramError as e:
        print(f"Xatolik yuz berdi ({target}): {e}")
        return False

async def reminder_scheduler(uid, r, context):
    pre_sent = False
    tz = r["time"].tzinfo  # vaqt zonasi

    while True:
        try:
            # Agar eslatma o'chirilgan bo'lsa, task to'xtaydi
            if r["id"] not in [x["id"] for x in users.get(uid, {}).get("reminders", [])]:
                break

            now = datetime.now(tz)

            # 🔹 Xavfsiz target_chat
            if r.get("bolm") == get_s(uid, "btn_personal"):
                target_chat = uid
            else:
                target_chat = r.get("link")
                if not target_chat:
                    print(f"⚠️ WARNING: link topilmadi, uid={uid}, bolm={r.get('bolm')}")
                    target_chat = uid

            # 🔔 OLDINDAN eslatma
            if r.get("pre_rem", 0) > 0 and not pre_sent:
                if now >= (r["time"] - timedelta(minutes=r["pre_rem"])):
                    if r.get("is_active", True):
                        await send_reminder(
                            context,
                            target_chat,
                            f"🔔 OLDINDAN ESLATMA ({r['pre_rem']} min qoldi):\n\n{r['text']}"
                        )
                    pre_sent = True

            # ⏰ Asosiy vaqt
            if now >= r["time"]:
                if r.get("is_active", True):
                    await send_reminder(
                        context,

                        target_chat,
                        f"⏰ VAQTI BO‘LDI:\n\n{r['text']}"
                    )

                # Agar takrorlansa
                if r.get("repeat"):
                    r["time"] += r["repeat"]
                    pre_sent = False
                    continue
                else:
                    r["is_active"] = False
                    users[uid].pop("edit_target", None)
                    break

            await asyncio.sleep(20)

        except Exception as e:
            print("Scheduler xato:", e)
            await asyncio.sleep(60)

async def reschedule_task(uid, r, context):
    if uid in tasks and r["id"] in tasks[uid]:
        tasks[uid][r["id"]].cancel()
    if uid not in tasks: tasks[uid] = {}
    tasks[uid][r["id"]] = asyncio.create_task(reminder_scheduler(uid, r, context))

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        users[uid] = {"reminders": [], "lang": "UZ", "tz": ZoneInfo("Asia/Tashkent")}
    kb = [["🇺🇿 O‘zbekcha", "🇷🇺 Русский"]]
    await update.message.reply_text(get_s(uid, "start"), reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return TIL

async def go_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users[uid].pop("current", None)
    users[uid].pop("edit_target", None)
    users[uid].pop("list_bolm", None)
    users[uid].pop("list_link", None)
    users[uid].pop("target_map", None)
    return await menu_display(update, context)

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in users:
        users[uid] = {
            "reminders": [],
            "lang": "UZ",
            "tz": ZoneInfo("Asia/Tashkent")
        }

    kb = [["🇺🇿 O‘zbekcha", "🇷🇺 Русский"]]

    await update.message.reply_text(
        get_s(uid, "start"),
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

    return TIL

async def set_time_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in users:
        users[uid] = {
            "reminders": [],
            "lang": "UZ",
            "tz": ZoneInfo("Asia/Tashkent")
        }

    await update.message.reply_text(
        get_s(uid, "ask_tz"),
        reply_markup=ReplyKeyboardRemove()
    )

    return MINTQA


async def til_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if "Рус" in text or "🇷🇺" in text:
        users[uid]["lang"] = "RU"
    else:
        users[uid]["lang"] = "UZ"

    await update.message.reply_text(
        get_s(uid, "ask_tz"),
        reply_markup=ReplyKeyboardRemove()
    )
    return MINTQA

async def mintqa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower().strip()

    zone = None
    for k, v in ZONE_MAP.items():
        if k in text:
            zone = v
            break

    # ❌ noto‘g‘ri mintaqa
    if not zone:
        await update.message.reply_text(
            "❌ Mintaqa topilmadi!\n\n"
            "👉 Faqat shularni kiriting:\n"
            "• Toshkent\n"
            "• Rossiya\n"
            "• New York\n\n"
            "📝 Ruscha yoki lotincha yozish mumkin"
        )
        return MINTQA

    # ✅ to‘g‘ri mintaqa
    users[uid]["tz"] = ZoneInfo(zone)
    return await menu_display(update, context)

async def menu_display(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    kb = [[get_s(uid, "btn_new")], [get_s(uid, "btn_list")]]
    await update.message.reply_text(get_s(uid, "menu"), reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # 🔙 Orqaga → asosiy menyu
    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)



    # ➕ Yangi eslatma
    if text == get_s(uid, "btn_new"):
        users[uid]["current"] = {
            "is_active": True,
            "id": str(uuid.uuid4())
        }

        kb = [
            [get_s(uid, "btn_personal"), get_s(uid, "btn_group"), get_s(uid, "btn_channel")],
            [get_s(uid, "btn_back")]
        ]

        await update.message.reply_text(
            get_s(uid, "ask_bolm"),
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return BOLM

    # 📋 Ro‘yxatlar
    elif text == get_s(uid, "btn_list"):
        kb = [
            [get_s(uid, "btn_personal"), get_s(uid, "btn_group"), get_s(uid, "btn_channel")],
            [get_s(uid, "btn_back")]
        ]

        await update.message.reply_text(
            get_s(uid, "ask_list_bolm"),  # ✅ TO‘G‘RI MATN
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return TAHRIR

    return MENU

async def bolm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    val = update.message.text

    # 🔙 Orqaga bosilgan bo‘lsa, asosiy menyuga qaytish
    if val == get_s(uid, "btn_back"):
        return await menu_display(update, context)

    # foydalanuvchi joriy bo‘limini saqlash
    users.setdefault(uid, {}).setdefault("current", {})["bolm"] = val

    # Shaxsiy bo‘lim
    if val == get_s(uid, "btn_personal"):
        await update.message.reply_text(
            get_s(uid, "ask_text"),
            reply_markup=ReplyKeyboardMarkup(
                [[get_s(uid, "btn_back")]],
                resize_keyboard=True
            )
        )
        return MATN

    # Guruh yoki Kanal bo‘limlari
    if val in [get_s(uid, "btn_group"), get_s(uid, "btn_channel")]:
        await update.message.reply_text(
            get_s(uid, "ask_link").format(val),
            reply_markup=ReplyKeyboardMarkup(
                [[get_s(uid, "btn_back")]],
                resize_keyboard=True
            )
        )
        return LINK

    # Agar boshqa xato kiritsa, menu qaytaradi
    return await menu_display(update, context)


def normalize_chat_id(text: str):
    """
    Foydalanuvchidan kiritilgan chat ID'ni to‘g‘rilaydi:
    - To‘liq superguruh / kanal ID (-100 bilan boshlanuvchi)
    - Qisqa manfiy ID → -100 bilan to‘g‘rilash
    - Noto‘g‘ri format → None
    """
    text = text.strip()

    if text.startswith("-100") and text[4:].isdigit():
        return int(text)

    if text.startswith("-") and text[1:].isdigit():
        return int("-100" + text[1:])

    return None


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    # 🔙 Orqaga bosilgan bo‘lsa, asosiy menyuga qaytish
    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)


    target = None

    # 1️⃣ ID orqali (maxfiy guruh / kanal)
    target = normalize_chat_id(text)

    # 2️⃣ Ochiq link orqali
    if not target and "t.me/" in text:
        username = text.split("t.me/")[-1].replace("/", "")
        target = "@" + username

    # 3️⃣ Ochiq username orqali
    if not target and text.startswith("@"):
        target = text

    # 4️⃣ Xato format
    if not target:
        await update.message.reply_text(
            "❌ Noto‘g‘ri format!\n\n"
            "🔒 Maxfiy guruh / kanal:\n"
            "   -1001234567890 yoki -5208369294\n\n"
            "📢 Ochiq kanal:\n"
            "   @kanal_nomi yoki https://t.me/kanal\n\n"
            "⬅️ Ortga qaytish tugmasi bilan asosiy menyuga qaytish mumkin",
            reply_markup=ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return LINK

    # Saqlash
    users[uid]["current"]["link"] = target
    await update.message.reply_text(
        get_s(uid, "ask_text"),
        reply_markup=ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )
    return MATN

async def matn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    target = users[uid].get("edit_target", users[uid]["current"])
    target["text"] = text
    if "edit_target" in users[uid]:
        return await tahrir_item_display(update, context)
    await update.message.reply_text(get_s(uid, "ask_time"))
    return VAQT

async def vaqt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    # 1. Xavfsizlik tekshiruvi: users[uid] mavjudligini tekshirish
    if uid not in users:
        users[uid] = {"reminders": [], "lang": "UZ", "tz": ZoneInfo("Asia/Tashkent")}
        return await start(update, context)

    # 2. "current" yoki "edit_target" borligini tekshirish
    # Agar bot restart bo'lsa yoki foydalanuvchi adashib vaqt yozsa, xato bermasligi uchun
    target = users[uid].get("edit_target") or users[uid].get("current")
    
    if not target:
        # Agar saqlanadigan obyekt bo'lmasa, menyuga qaytaradi
        return await menu_display(update, context)

    tz = users[uid].get("tz", ZoneInfo("Asia/Tashkent"))
    text = update.message.text.strip()
    
    try:
        # Sana va vaqtni parse qilish
        if ":" in text:
            dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
        else:
            dt = datetime.strptime(text, "%d.%m.%Y")
            dt = dt.replace(hour=9, minute=0)
        
        # Vaqt zonasini biriktirish
        dt = dt.replace(tzinfo=tz)
        now = datetime.now(tz)
        
        # Vaqt o'tib ketmaganini tekshirish
        if dt < now:
            await update.message.reply_text(get_s(uid, "error_time"))
            return VAQT
        
        # Vaqtni saqlash
        target["time"] = dt
        
        # Agar tahrirlash rejimi bo'lsa
        if "edit_target" in users[uid]:
            await reschedule_task(uid, target, context)
            return await tahrir_item_display(update, context)
        
        # Agar yangi eslatma bo'lsa, takrorlashni so'rash
        await update.message.reply_text(
            get_s(uid, "ask_rep"), 
            reply_markup=ReplyKeyboardMarkup(get_rep_kb(uid), resize_keyboard=True)
        )
        return TAKROR

    except ValueError:
        # Format noto'g'ri bo'lsa
        await update.message.reply_text(get_s(uid, "error_time"))
        return VAQT

# await update.message.reply_text("Masalan: 15.01.2026 14:00")


async def takror_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    td = None

    # Tilga qarab matnlar
    lang = users[uid]["lang"]
    rep_map = {
        "UZ": {
            "Har kuni": timedelta(days=1),
            "Har hafta": timedelta(weeks=1),
            "2 haftada": timedelta(weeks=2),
            "Har oy": timedelta(days=30),
            "3 oyda": timedelta(days=90),
            "6 oyda": timedelta(days=180),
            "Har yili": timedelta(days=365),
            "Hech qachon": None
        },
        "RU": {
            "Каждый день": timedelta(days=1),
            "Каждую неделю": timedelta(weeks=1),
            "Каждые 2 недели": timedelta(weeks=2),
            "Каждый месяц": timedelta(days=30),
            "Каждые 3 месяца": timedelta(days=90),
            "Каждые 6 месяцев": timedelta(days=180),
            "Каждый год": timedelta(days=365),
            "Никогда": None
        }
    }

    if text in rep_map[lang]:
        td = rep_map[lang][text]
    elif "Qo'lda" in text or "Вручную" in text:
        await update.message.reply_text("✍️ Masalan: 2 kun, 5 soat yoki 1 hafta:" if lang=="UZ" else "✍️ Например: 2 дня, 5 часов или 1 неделя:")
        return TAKROR
    else:
        td = parse_duration(text)

    target = users[uid].get("edit_target", users[uid]["current"])
    target["repeat"] = td

    if "edit_target" in users[uid]:
        await reschedule_task(uid, target, context)
        return await tahrir_item_display(update, context)

    await update.message.reply_text(get_s(uid, "ask_pre"), reply_markup=ReplyKeyboardMarkup(get_pre_kb(uid), resize_keyboard=True))
    return OLDINDAN



async def oldindan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower()
    lang = users[uid]["lang"]
    pre = None

    # Agar foydalanuvchi qo'lda vaqt kiritmoqchi bo'lsa
    if lang == "UZ" and "qo'lda" in text:
        await update.message.reply_text("✍️ Masalan: 10 daqiqa yoki 1 soat:")
        return OLDINDAN
    elif lang == "RU" and "вручную" in text:
        await update.message.reply_text("✍️ Например: 10 минут или 1 час:")
        return OLDINDAN

    # Raqamlarni textdan topish
    nums = re.findall(r'\d+', text)
    if not nums:
        if lang == "UZ":
            await update.message.reply_text("❌ Vaqt topilmadi!")
        else:
            await update.message.reply_text("❌ Время не найдено!")
        return OLDINDAN

    n = int(nums[0])

    # Birliklarni tekshirish
    if lang == "UZ":
        if any(w in text for w in ["daqiqa", "minut"]):
            pre = n
        elif "soat" in text:
            pre = n * 60
        elif "kun" in text:
            pre = n * 1440
    else:  # RU
        if any(w in text for w in ["минута", "минуты", "минут"]):
            pre = n
        elif any(w in text for w in ["час", "часа", "часов"]):
            pre = n * 60
        elif any(w in text for w in ["день", "дня", "дней"]):
            pre = n * 1440

    if pre is None or pre <= 0:
        if lang == "UZ":
            await update.message.reply_text("❌ Vaqt topilmadi!")
        else:
            await update.message.reply_text("❌ Время не найдено!")
        return OLDINDAN

    # Target olish va reminder sozlash
    target = users[uid].get("edit_target", users[uid]["current"])
    target["pre_rem"] = pre

    if "edit_target" in users[uid]:
        await reschedule_task(uid, target, context)
        return await tahrir_item_display(update, context)

    users[uid]["reminders"].append(target)
    await reschedule_task(uid, target, context)

    if lang == "UZ":
        await update.message.reply_text(get_s(uid, "success"))
    else:
        await update.message.reply_text(get_s(uid, "success_ru"))

    return await menu_display(update, context)


# ===== EDIT & LIST =====
async def tahrir_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    btn_personal = get_s(uid, "btn_personal")
    btn_group = get_s(uid, "btn_group")
    btn_channel = get_s(uid, "btn_channel")
    btn_back = get_s(uid, "btn_back")

    # 1. 🔙 ORQAGA BOSILSA
    if text == btn_back:
        users[uid].pop("list_bolm", None)
        users[uid].pop("target_map", None)
        return await menu_display(update, context)

    # 2. AGAR GURUH/KANAL NOMI TANLANGAN BO'LSA (target_map ichidan qidiramiz)
    if "target_map" in users[uid] and text in users[uid]["target_map"]:
        selected_link = users[uid]["target_map"][text]
        # Shu tanlangan manzilga tegishli barcha eslatmalarni filtrlaymiz
        items = [r for r in users[uid]["reminders"] if str(r.get("link")) == str(selected_link)]
        
        if not items:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        # Eslatmalar ro'yxatini chiqarish
        kb = [[f"📌 {r['text'][:30]}"] for r in items]
        kb.append([btn_back])
        
        await update.message.reply_text(
            f"📝 {text} — eslatmalari:" if users[uid]["lang"] == "UZ" else f"📝 {text} — заметки:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return EXIT_EDIT

    # 3. SHAXSIY BO'LIM TANLANSA
    if text == btn_personal:
        items = [r for r in users[uid]["reminders"] if r["bolm"] == btn_personal]
        if not items:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        kb = [[f"📌 {r['text'][:30]}"] for r in items]
        kb.append([btn_back])
        await update.message.reply_text(
            "✏️ Shaxsiy eslatmalar:" if users[uid]["lang"] == "UZ" else "✏️ Личные заметки:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return EXIT_EDIT

    # 4. GURUH YOKI KANAL TUGMASI BOSILSA (Guruhlar ro'yxatini shakllantirish)
    if text in [btn_group, btn_channel]:
        users[uid]["list_bolm"] = text
        users[uid]["target_map"] = {}
        kb = []
        seen = set()

        for r in users[uid]["reminders"]:
            if r["bolm"] == text:
                link = str(r.get("link"))
                if link not in seen:
                    seen.add(link)
                    try:
                        # Guruh/Kanal nomini Telegramdan olamiz
                        chat = await context.bot.get_chat(link)
                        name = chat.title or chat.username or link
                    except:
                        name = link
                    
                    kb.append([name])
                    users[uid]["target_map"][name] = link

        if not kb:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        kb.append([btn_back])
        await update.message.reply_text(
            "📂 Kerakli manzilni tanlang:" if users[uid]["lang"] == "UZ" else "📂 Выберите адрес:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return TAHRIR # Shunda foydalanuvchi guruh nomini bossa, funksiya qayta ishlaydi va 2-punktga tushadi

    # 5. AGAR NOTO'G'RI MATN KIRITILSA (Boshlang'ich bo'lim tanlash)
    kb = [[btn_personal, btn_group, btn_channel], [btn_back]]
    msg = "📋 Bo'limni tanlang:" if users[uid]["lang"] == "UZ" else "📋 Выберите раздел:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return TAHRIR

async def tahrir_item_display(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    r = users[uid]["edit_target"]
    kb = [
        [get_s(uid, "btn_edit_text"), get_s(uid, "btn_edit_time")],
        [get_s(uid, "btn_edit_rep"), get_s(uid, "btn_edit_pre")],
        [get_s(uid, "btn_toggle"), get_s(uid, "btn_del")],
        [get_s(uid, "btn_back")]
    ]
    await update.message.reply_text(format_reminder_text(uid, r), reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return EXIT_EDIT

async def exit_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # 🔙 Orqaga
    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    # =================================================
    # 📌 ESLATMANI TANLASH (ID YO‘Q → MATN ORQALI)
    # =================================================
    if "edit_target" not in users[uid]:
        for r in users[uid]["reminders"]:
            if r["text"][:30] in text:
                users[uid]["edit_target"] = r
                return await tahrir_item_display(update, context)

    # Agar hali ham tanlanmagan bo‘lsa
    r = users[uid].get("edit_target")
    if not r:
        return MENU

    # =========================
    # ✏️ TAHRIR AMALLARI
    # =========================
    if text == get_s(uid, "btn_edit_text"):
        await update.message.reply_text(
            get_s(uid, "ask_text"),
            reply_markup=ReplyKeyboardRemove()
        )
        return MATN

    elif text == get_s(uid, "btn_edit_time"):
        await update.message.reply_text(
            get_s(uid, "ask_time"),
            reply_markup=ReplyKeyboardRemove()
        )
        return VAQT

    elif text == get_s(uid, "btn_edit_rep"):
        await update.message.reply_text(
            get_s(uid, "ask_rep"),
            reply_markup=ReplyKeyboardMarkup(get_rep_kb(uid), resize_keyboard=True)  # ✅ uid qo'shildi
        )
        return TAKROR

    elif text == get_s(uid, "btn_edit_pre"):
        await update.message.reply_text(
            get_s(uid, "ask_pre"),
            reply_markup=ReplyKeyboardMarkup(get_pre_kb(uid), resize_keyboard=True)  # ✅ uid qo'shildi
        )
        return OLDINDAN

    # ✅ ENG MUHIM JOY — TOGGLE
    elif text == get_s(uid, "btn_toggle"):
        r["is_active"] = not r["is_active"]

        # 🔁 scheduler qayta sozlanadi
        await reschedule_task(uid, r, context)

        return await tahrir_item_display(update, context)

    # 🗑 O‘CHIRISH
    elif text == get_s(uid, "btn_del"):
        users[uid]["reminders"] = [
            x for x in users[uid]["reminders"]
            if x["id"] != r["id"]
        ]

        if r["id"] in tasks.get(uid, {}):
            tasks[uid][r["id"]].cancel()

        users[uid].pop("edit_target", None)
        return await menu_display(update, context)

    return EXIT_EDIT


def back_filter():
    return filters.Regex(r"^⬅️")

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("change_lang", change_lang),
            CommandHandler("set_time_zone", set_time_zone),
        ],
        states={
            TIL: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, til_handler),
            ],
            MINTQA: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, mintqa_handler),
            ],
            MENU: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler),
            ],
            BOLM: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bolm_handler),
            ],
            LINK: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler),
            ],
            MATN: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, matn_handler),
            ],
            VAQT: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, vaqt_handler),
            ],
            TAKROR: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, takror_handler),
            ],
            OLDINDAN: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, oldindan_handler),
            ],
           TAHRIR: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tahrir_list),
            ],
           EXIT_EDIT: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, exit_edit_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(conv)

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()

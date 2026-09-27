import datetime

import telebot
from telebot import types

from config import BOT_TOKEN, ADMIN_CHAT_ID
from sites import get_sites_text, get_site_names, get_site_by_name, get_site_by_slug
from storage import save_order, get_user_orders
from healthcheck import start_health_server_in_background

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Foydalanuvchi tasdiqlashini kutayotgan buyurtmalar (order_id berilmasdan oldingi holat).
# Kalit: foydalanuvchi Telegram ID'si.
pending_orders = {}


# ---------------------------------------------------------
# Asosiy menyu (Reply Keyboard)
# ---------------------------------------------------------

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Saytlar"),
        types.KeyboardButton("📦 Buyurtma berish"),
    )
    markup.add(
        types.KeyboardButton("📋 Mening buyurtmalarim"),
        types.KeyboardButton("📞 Aloqa"),
    )
    markup.add(types.KeyboardButton("ℹ️ Yordam"))
    return markup


# ---------------------------------------------------------
# /start
# ---------------------------------------------------------

@bot.message_handler(commands=["start"])
def handle_start(message):
    # Sayt Market saytidagi "Buyurtma" tugmasi https://t.me/Yetkazib_beruvchi_bot?start=SLUG
    # ko'rinishida keladi. Shu parametr orqali foydalanuvchi qaysi saytga
    # qiziqqanini avvaldan bilib, buyurtma jarayonini shu bilan boshlaymiz.
    parts = message.text.split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else None
    preselected_site = get_site_by_slug(payload)

    text = (
        "👋 Assalomu alaykum, <b>Sayt Market</b> botiga xush kelibsiz!\n\n"
        "Bu yerda siz mavjud saytlar katalogini ko'rishingiz va ular orqali "
        "buyurtma berishingiz mumkin.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

    if preselected_site:
        msg = bot.send_message(
            message.chat.id,
            (
                f"Siz saytdan <b>{preselected_site['name']}</b> xizmatiga "
                "qiziqish bildirdingiz.\n\n"
                "Buyurtma berishni davom ettiramiz.\n📝 Ismingizni kiriting:"
            ),
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.register_next_step_handler(msg, process_name_step, preselected_site["name"])


# ---------------------------------------------------------
# 🛒 Saytlar
# ---------------------------------------------------------

@bot.message_handler(commands=["saytlar"])
@bot.message_handler(func=lambda m: m.text == "🛒 Saytlar")
def handle_sites(message):
    bot.send_message(message.chat.id, get_sites_text(), reply_markup=main_menu())


# ---------------------------------------------------------
# 📞 Aloqa
# ---------------------------------------------------------

@bot.message_handler(commands=["aloqa"])
@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def handle_contact(message):
    text = (
        "📞 <b>Biz bilan aloqa:</b>\n\n"
        "Telegram: @your_admin_username\n"
        "Telefon: +998 90 123 45 67\n"
        "Email: info@saytmarket.uz"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


# ---------------------------------------------------------
# ℹ️ Yordam
# ---------------------------------------------------------

@bot.message_handler(commands=["yordam"])
@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def handle_help(message):
    text = (
        "ℹ️ <b>Yordam</b>\n\n"
        "/start — Botni ishga tushirish\n"
        "/saytlar — Saytlar katalogini ko'rish\n"
        "/buyurtma — Yangi buyurtma berish\n"
        "/aloqa — Biz bilan bog'lanish\n"
        "/yordam — Ushbu yordam matni\n\n"
        "Savollaringiz bo'lsa, «📞 Aloqa» bo'limiga murojaat qiling."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


# ---------------------------------------------------------
# 📋 Mening buyurtmalarim
# ---------------------------------------------------------

@bot.message_handler(func=lambda m: m.text == "📋 Mening buyurtmalarim")
def handle_my_orders(message):
    orders = get_user_orders(message.from_user.id)
    if not orders:
        bot.send_message(
            message.chat.id,
            "📋 Sizda hozircha buyurtmalar yo'q.",
            reply_markup=main_menu(),
        )
        return

    lines = ["📋 <b>Sizning buyurtmalaringiz:</b>\n"]
    for o in orders:
        lines.append(
            f"🔸 Buyurtma #{o['order_id']}\n"
            f"🛒 Sayt: {o['site']}\n"
            f"📍 Qayerdan: {o['location']}\n"
            f"🗓 Qachonga kerak: {o['needed_by']}\n"
            f"Sana: {o['date']}\n"
        )
    bot.send_message(message.chat.id, "\n".join(lines), reply_markup=main_menu())


# ---------------------------------------------------------
# 📦 Buyurtma berish — ketma-ket so'rov:
# ism -> telefon -> qayerdanligi -> qachonga kerak -> (kerak bo'lsa) sayt -> tasdiqlash
# ---------------------------------------------------------

@bot.message_handler(commands=["buyurtma"])
@bot.message_handler(func=lambda m: m.text == "📦 Buyurtma berish")
def handle_order_start(message):
    msg = bot.send_message(
        message.chat.id,
        "📝 Buyurtma berishni boshlaymiz.\n\nIltimos, <b>ismingizni</b> kiriting:",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message, preselected_site_name=None):
    name = message.text
    msg = bot.send_message(
        message.chat.id,
        "📱 Endi <b>telefon raqamingizni</b> kiriting:\n(masalan: +998901234567)",
    )
    bot.register_next_step_handler(msg, process_phone_step, name, preselected_site_name)


def process_phone_step(message, name, preselected_site_name=None):
    phone = message.text
    msg = bot.send_message(
        message.chat.id,
        "📍 Qayerdansiz? (shahringiz yoki manzilingizni yozing)",
    )
    bot.register_next_step_handler(
        msg, process_location_step, name, phone, preselected_site_name
    )


def process_location_step(message, name, phone, preselected_site_name=None):
    location = message.text
    msg = bot.send_message(
        message.chat.id,
        "🗓 Sayt sizga <b>qachonga kerak</b>? (masalan: tezroq, 1 hafta ichida, aniq sana)",
    )
    bot.register_next_step_handler(
        msg, process_deadline_step, name, phone, location, preselected_site_name
    )


def process_deadline_step(message, name, phone, location, preselected_site_name=None):
    needed_by = message.text

    # Agar sayt Sayt Market'dagi tugma orqali avvaldan aniq bo'lsa, qayta so'ramaymiz.
    if preselected_site_name:
        show_confirmation(message, name, phone, location, needed_by, preselected_site_name)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for site_name in get_site_names():
        markup.add(types.KeyboardButton(site_name))

    msg = bot.send_message(
        message.chat.id,
        "🛒 Qaysi <b>sayt</b>dan buyurtma bermoqchisiz?",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, process_site_step, name, phone, location, needed_by)


def process_site_step(message, name, phone, location, needed_by):
    site = get_site_by_name(message.text)
    site_display = site["name"] if site else message.text
    show_confirmation(message, name, phone, location, needed_by, site_display)


def show_confirmation(message, name, phone, location, needed_by, site_display):
    """Yig'ilgan ma'lumotlarni ko'rsatib, foydalanuvchidan tasdiqlashni so'raydi."""
    pending_orders[message.from_user.id] = {
        "name": name,
        "phone": phone,
        "location": location,
        "needed_by": needed_by,
        "site": site_display,
    }

    summary = (
        "🧾 <b>Buyurtmangizni tekshiring:</b>\n\n"
        f"👤 Ism: {name}\n"
        f"📱 Telefon: {phone}\n"
        f"📍 Qayerdan: {location}\n"
        f"🗓 Qachonga kerak: {needed_by}\n"
        f"🛒 Sayt: {site_display}\n\n"
        "Hammasi to'g'rimi?"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_order"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_order"),
    )
    bot.send_message(
        message.chat.id,
        summary,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data in ("confirm_order", "cancel_order"))
def handle_order_confirmation(call):
    user_id = call.from_user.id

    if call.data == "cancel_order":
        pending_orders.pop(user_id, None)
        bot.edit_message_text(
            "❌ Buyurtma bekor qilindi.",
            call.message.chat.id,
            call.message.message_id,
        )
        bot.send_message(
            call.message.chat.id,
            "Menyudan xohlagan bo'limni tanlashingiz mumkin 👇",
            reply_markup=main_menu(),
        )
        bot.answer_callback_query(call.id)
        return

    order = pending_orders.pop(user_id, None)
    if not order:
        bot.answer_callback_query(
            call.id, "Bu buyurtma muddati o'tgan. Iltimos, qaytadan boshlang.", show_alert=True
        )
        return

    order["user_id"] = user_id
    order["username"] = call.from_user.username
    order["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    order_id = save_order(order)

    bot.edit_message_text(
        (
            "✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
            f"🔸 Buyurtma raqami: #{order_id}\n\n"
            "Tez orada operatorlarimiz siz bilan bog'lanishadi."
        ),
        call.message.chat.id,
        call.message.message_id,
    )
    bot.send_message(call.message.chat.id, "Menyu:", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

    if ADMIN_CHAT_ID:
        admin_text = (
            "🆕 <b>Yangi buyurtma!</b>\n\n"
            f"🔸 Buyurtma raqami: #{order_id}\n"
            f"👤 Ism: {order['name']}\n"
            f"📱 Telefon: {order['phone']}\n"
            f"📍 Qayerdan: {order['location']}\n"
            f"🗓 Qachonga kerak: {order['needed_by']}\n"
            f"🛒 Sayt: {order['site']}\n"
            f"🆔 Foydalanuvchi: @{call.from_user.username or 'nomsiz'} (ID: {user_id})"
        )
        try:
            bot.send_message(ADMIN_CHAT_ID, admin_text)
        except Exception as e:
            print(f"Admin xabar yuborishda xatolik: {e}")


# ---------------------------------------------------------
# Noma'lum xabarlar
# ---------------------------------------------------------

@bot.message_handler(func=lambda m: True)
def handle_unknown(message):
    bot.send_message(
        message.chat.id,
        "Kechirasiz, bu buyruqni tushunmadim 🤔\nMenyudan foydalaning yoki /yordam ni bosing.",
        reply_markup=main_menu(),
    )


if __name__ == "__main__":
    start_health_server_in_background()
    print("Bot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)

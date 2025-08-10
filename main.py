import json
import os
from datetime import datetime, timedelta
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

TOKEN = '7705891566:AAETdc4uIOJJXDeGPw9jKOiTy-A7SSjkasQ'  # Бот токен
ADMIN_ID = 7398183328  # Админ ID

DATA_FILE = "bot_data.json"

CHOOSING, LOCATION, PHONE, BROADCAST = range(4)

# 📂 Деректерді оқу
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": [], "orders": []}

# 💾 Деректерді сақтау
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 📌 Бот деректері
bot_data = load_data()

# Ескі форматтағы user тізімін жаңарту
for i, u in enumerate(bot_data["users"]):
    if isinstance(u, int):  # ескі формат (тек ID)
        bot_data["users"][i] = {
            "id": u,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
save_data(bot_data)

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    today = datetime.now().strftime("%Y-%m-%d")

    # Жаңа қолданушы болса — тізімге қосамыз
    if not any(u["id"] == user_id for u in bot_data["users"]):
        bot_data["users"].append({"id": user_id, "date": today})
        save_data(bot_data)

        # Админге хабар жіберу
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "(username жоқ)"
        message = (
            f"🆕 Жаңа пайдаланыушы\n\n"
            f"👤 Аты: {full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"🔗 Username: {username}"
        )
        context.bot.send_message(chat_id=ADMIN_ID, text=message)

    # Кнопкалар
    buttons = [['ШЫМБАЙ ➡️ НӨКІС', 'НӨКІС ➡️ ШЫМБАЙ']]
    if user_id == ADMIN_ID:
        buttons.append(['📊 Статистика', '📢 Хабарлама жіберу'])

    update.message.reply_text(
        "🚖 АССАЛАУМА ӘЛЕЙКУМ ХОШ КЕЛДИҢИЗ!\n\n"
        "📍 Біз \n\n"
        "↗️ ШЫМБАЙДАН ➡️ НУКУСГЕ \n\n"
        "↙️ НУКУСТЕН ⬅️ ШЫМБАЙҒА \n\n"
        "📍мәнзилден-мәнзилге такси хизметин ұсынамыз!\n\n"
        "📦 Аманат почталарыңызды мәнзилиңизге жеткеремиз!\n •БИЗДЕ ТӨБЕ БАГАЖ ХИЗМЕТИ БАР \n\n"
        "📞 +998770149797\n📞+998770149797\n\n"
        "👨‍💻@rakhim753\n\n"
        "ТӨМЕНДЕГИ КНОПКАЛАРДАН ОЗИҢИЗГЕ КЕРЕКЛИ МӘНЗИЛДИ ТАҢЛАҢ😊:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
    return CHOOSING

def choose_route(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "📊 Статистика":
        return show_stats(update, context)

    if text == "📢 Хабарлама жіберу" and update.message.from_user.id == ADMIN_ID:
        update.message.reply_text(
            "✍️ Қандай хабарлама жібереміз? (хабарламаны жазың):",
            reply_markup=ReplyKeyboardRemove()
        )
        return BROADCAST

    context.user_data['route'] = text
    location_button = [[KeyboardButton("📍 Локация жіберу", request_location=True)]]
    update.message.reply_text(
        "📍 Илтимас өз мәнзилиңизди кнопка арқалы жибериң:",
        reply_markup=ReplyKeyboardMarkup(location_button, resize_keyboard=True)
    )
    return LOCATION

def get_location(update: Update, context: CallbackContext):
    location = update.message.location
    context.user_data['location'] = f"https://maps.google.com/?q={location.latitude},{location.longitude}"
    update.message.reply_text(
        "📞 Енді телефон номеріңізді хәм адам санын жазың (мысалы: +998901234567 2АДАМ):",
        reply_markup=ReplyKeyboardRemove()
    )
    return PHONE

def get_phone(update: Update, context: CallbackContext):
    phone = update.message.text
    route = context.user_data['route']
    location = context.user_data['location']

    message = f"🚖 Жаңа буйыртпа:\n\n🛣 Мәнзил: {route}\n📍 Локация: {location}\n📞 Номер: {phone}"
    context.bot.send_message(chat_id=ADMIN_ID, text=message)

    bot_data["orders"].append({
        "route": route,
        "location": location,
        "phone": phone
    })
    save_data(bot_data)

    update.message.reply_text(
        "✅ Бизди таңлағаныңыз ушын рахмет😊\nБас менюге қайтыу үшін /start басың.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def show_stats(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("❌ Бұл бөлім тек админге арналған.")
        return CHOOSING

    order_count = len(bot_data["orders"])
    user_count = len(bot_data["users"])

    today = datetime.now().strftime("%Y-%m-%d")
    last_7_days = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    today_users = sum(1 for u in bot_data["users"] if u["date"] == today)
    week_users = sum(1 for u in bot_data["users"] if u["date"] in last_7_days)

    text = f"📊 *Статистика:*\n" \
           f"👤 Барлық пайдаланушылар: {user_count}\n" \
           f"📦 Барлық буйыртпалар: {order_count}\n" \
           f"📅 Бүгін қосылғанлар: {today_users}\n" \
           f"📆 Соңғы 7 күнде қосылғанлар: {week_users}\n\n"

    last_orders = bot_data["orders"][-5:]
    for i, order in enumerate(last_orders, 1):
        text += (
            f"#{i}\n"
            f"🛣 Мәнзил: {order['route']}\n"
            f"📍 Локация: {order['location']}\n"
            f"📞 Номер: {order['phone']}\n\n"
        )

    update.message.reply_text(text, parse_mode='Markdown')
    return CHOOSING

def broadcast(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return CHOOSING

    message = update.message.text
    success = 0
    for user in bot_data["users"]:
        try:
            context.bot.send_message(chat_id=user["id"], text=message)
            success += 1
        except:
            continue

    update.message.reply_text(f"📢 Хабарлама {success} пайдаланыушыға жіберілді.")
    return CHOOSING

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Бийкар етилди.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSING: [MessageHandler(Filters.text & ~Filters.command, choose_route)],
        LOCATION: [MessageHandler(Filters.location, get_location)],
        PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
        BROADCAST: [MessageHandler(Filters.text & ~Filters.command, broadcast)],
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        CommandHandler('start', start)
    ]
)

dp.add_handler(conv_handler)
updater.start_polling()
updater.idle()
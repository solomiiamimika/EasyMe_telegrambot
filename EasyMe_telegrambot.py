from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler,
    filters
)
import json
from geopy.distance import distance
import os

BOT_TOKEN = "7421424417:AAH1norish7VoznWvbvnzTv2FaTRj5LQwJk"  # встав свій реальний токен сюди

REGISTER_NAME = 0
ORDER_SERVICE, ORDER_AREA, ORDER_TIME, ORDER_COMMENT = range(4)

SERVICE_OPTIONS = [
    "Купити продукти", "Приготувати їжу",
    "Масаж", "Подати таблетки",
    "Прибирання", "Будь-яка робота"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Привіт! Я EasyMe бот</b>\n\n"
        "Я допомагаю знаходити виконавців і замовлення поруч.\n\n"
        "➡️ /register — стати виконавцем\n"
        "➡️ /order — створити замовлення\n"
        "➡️ /nearby — подивитися замовлення поруч",
        parse_mode='HTML'
    )

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Як вас звати?")
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    context.user_data["selected_services"] = []
    keyboard = build_service_keyboard([])
    await update.message.reply_text(
        "📌 Оберіть, що ви можете робити (можна кілька):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

def build_service_keyboard(selected):
    keyboard = []
    row = []
    for i, service in enumerate(SERVICE_OPTIONS):
        check = "✅" if service in selected else "▫️"
        button = InlineKeyboardButton(f"{check} {service}", callback_data=f"toggle_{i}")
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="done")])
    return keyboard

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    context.user_data["location"] = {
        "lat": location.latitude,
        "lon": location.longitude
    }

    await update.message.reply_text("📍 Локацію збережено!")

    if "availability" not in context.user_data:
        await ask_availability(update, context)
        return

    profile = {
        "id": generate_worker_id(),
        "user_id": update.effective_user.id,
        "name": context.user_data['name'],
        "services": context.user_data['services'],
        "area": context.user_data['area'],
        "availability": context.user_data['availability'],
        "location": context.user_data["location"],
        "rating": 0
    }

    save_worker(profile)

    await update.message.reply_text(
        "🌸 Ви зареєстровані як виконавець! Тепер можете переглянути /nearby замовлення поруч 🛠️",
        parse_mode='HTML'
    )

def save_worker(worker):
    try:
        with open("workers.json", "r", encoding="utf-8") as f:
            workers = json.load(f)
    except FileNotFoundError:
        workers = []

    workers.append(worker)

    with open("workers.json", "w", encoding="utf-8") as f:
        json.dump(workers, f, indent=2, ensure_ascii=False)

def generate_worker_id():
    try:
        with open("workers.json", "r", encoding="utf-8") as f:
            workers = json.load(f)
            return len(workers) + 1
    except:
        return 1

async def nearby_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        with open("workers.json", "r", encoding="utf-8") as f:
            workers = json.load(f)
    except FileNotFoundError:
        await update.message.reply_text("📂 Дані виконавців не знайдено. Пройдіть реєстрацію.")
        return

    worker = next((w for w in workers if w["user_id"] == user_id), None)

    if not worker or not worker.get("location") or not worker["location"].get("lat"):
        await update.message.reply_text("😕 Спочатку пройдіть реєстрацію з геолокацією (/register)")
        return

    user_loc = (worker["location"]["lat"], worker["location"]["lon"])

    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
    except FileNotFoundError:
        await update.message.reply_text("📦 База замовлень порожня.")
        return

    filtered = []
    for order in orders:
        if order["status"] != "нове" or not order.get("lat") or not order.get("lon"):
            continue
        order_loc = (order["lat"], order["lon"])
        dist_km = round(distance(user_loc, order_loc).km, 2)
        order["distance"] = dist_km
        filtered.append(order)

    if not filtered:
        await update.message.reply_text("😔 Поруч немає активних замовлень.")
        return

    filtered.sort(key=lambda x: x["distance"])
    top3 = filtered[:3]

    for order in top3:
        gmaps_link = f"https://www.google.com/maps/dir/{user_loc[0]},{user_loc[1]}/{order['lat']},{order['lon']}"
        msg = (
            f"🔧 <b>{order['service']}</b>\n"
            f"📍 <i>{order['area']}</i> — {order['distance']} км\n"
            f"🕒 {order['time']}\n\n"
            f"➡️ <a href='{gmaps_link}'>📍 Побудувати маршрут</a>\n"
            f"➡️ /take_{order['id']}"
        )
        await update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)

def generate_order_id():
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
            return len(orders) + 1
    except:
        return 1

def save_order(order):
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
    except FileNotFoundError:
        orders = []

    orders.append(order)

    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = build_service_keyboard([])
    await update.message.reply_text(
        "🛒 Оберіть, яку послугу ви хочете замовити:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data["order"] = {}
    return ORDER_SERVICE

async def order_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "toggle_" in query.data:
        index = int(query.data.split("_")[1])
        service = SERVICE_OPTIONS[index]
        selected = context.user_data.get("order_services", [])

        if service in selected:
            selected.remove(service)
        else:
            selected.append(service)

        context.user_data["order_services"] = selected
        keyboard = build_service_keyboard(selected)
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "done":
        selected = context.user_data.get("order_services", [])
        if not selected:
            await query.answer("❗ Виберіть хоча б одну послугу", show_alert=True)
            return

        context.user_data["order"]["service"] = selected[0]
        await query.edit_message_text("📍 У якому районі потрібна послуга?")
        return ORDER_AREA

async def order_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["area"] = update.message.text
    await update.message.reply_text(
        "⏰ Коли бажано виконати замовлення?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Ранок", callback_data="time_Ранок")],
            [InlineKeyboardButton("День", callback_data="time_День")],
            [InlineKeyboardButton("Вечір", callback_data="time_Вечір")],
            [InlineKeyboardButton("Будь-коли", callback_data="time_any")]
        ])
    )
    return ORDER_TIME

async def order_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    time = query.data.split("_")[1]
    context.user_data["order"]["time"] = time
    await query.edit_message_text("✍️ Бажаєте додати коментар до замовлення?")
    return ORDER_COMMENT

async def order_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["comment"] = update.message.text
    order = context.user_data["order"]
    order["id"] = generate_order_id()
    order["status"] = "нове"
    order["user_id"] = update.effective_user.id
    order["lat"] = None
    order["lon"] = None

    save_order(order)

    await update.message.reply_text("✅ Замовлення збережено! Очікуйте виконавця ✨")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    register_conversation = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        },
        fallbacks=[]
    )

    order_conversation = ConversationHandler(
        entry_points=[CommandHandler("order", order_start)],
        states={
            ORDER_SERVICE: [CallbackQueryHandler(order_service_callback)],
            ORDER_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_area)],
            ORDER_TIME: [CallbackQueryHandler(order_time_callback)],
            ORDER_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_comment)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(register_conversation)
    app.add_handler(order_conversation)
    app.add_handler(CallbackQueryHandler(order_service_callback))  # shared
    app.add_handler(CommandHandler("nearby", nearby_orders))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))

    print("🤖 EasyMe бот запущено!")
    app.run_polling()


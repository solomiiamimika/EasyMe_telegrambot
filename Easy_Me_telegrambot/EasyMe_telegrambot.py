from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, CallbackQueryHandler,
   
)
import json
from geopy.distance import distance
import os

# 🔐 ВСТАВ СЮДИ СВІЙ БОТ-ТOKEN
BOT_TOKEN = "7421424417:AAH1norish7VoznWvbvnzTv2FaTRj5LQwJk"

REGISTER_NAME = 0

SERVICE_OPTIONS = [
    "Купити продукти", "Приготувати їжу",
    "Масаж", "Подати таблетки",
    "Прибирання", "Будь-яка робота"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists(r"D:\Solomiia Python\Me_safespace_bot\easyme_logo.png"):
        with open(r"D:\Solomiia Python\Me_safespace_bot\easyme_logo.png", "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=(
                    "👋 <b>Привіт! Я EasyMe бот</b>\n\n"
                    "Я допомагаю швидко знаходити виконавців для побутових задач 👩‍🍳🧼💊\n\n"
                    "➡️ Щоб зареєструватися як виконавець, напиши <b>/register</b>\n"
                    "➡️ Щоб подивитися замовлення поруч — <b>/nearby</b>\n\n"
                    "Готові допомагати один одному? 🧡"
                ),
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "👋 <b>Привіт! Я EasyMe бот</b>\n\n"
            "🖼️ (Логотип не знайдено, але я працюю!)\n"
            "➡️ /register щоб зареєструватися\n"
            "➡️ /nearby щоб переглянути замовлення 🛠️",
            parse_mode='HTML'
        )

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Як вас звати?")
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    context.user_data["selected_services"] = []
    keyboard = build_service_keyboard(context.user_data["selected_services"])
    await update.message.reply_text(
        "📌 Оберіть, що ви можете робити (можна кілька). Натисніть '✅ Готово', коли все:",
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

async def ask_area(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Schwabing", callback_data="area_Schwabing"),
         InlineKeyboardButton("Glockenbach", callback_data="area_Glockenbach")],
        [InlineKeyboardButton("Moosach", callback_data="area_Moosach"),
         InlineKeyboardButton("Neuhausen", callback_data="area_Neuhausen")],
        [InlineKeyboardButton("🏙️ Будь-який район", callback_data="area_any")]
    ]
    await update_or_query.message.reply_text("🏙️ Оберіть район, де ви готові працювати:",
                                             reply_markup=InlineKeyboardMarkup(keyboard))

async def ask_location(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Надіслати геолокацію", request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update_or_query.message.reply_text(
        "📍 Поділись, де ти зараз знаходишся:",
        reply_markup=keyboard
    )

async def ask_availability(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Ранок (8:00–11:00)", callback_data="time_Ранок")],
        [InlineKeyboardButton("День (12:00–17:00)", callback_data="time_День")],
        [InlineKeyboardButton("Вечір (18:00–22:00)", callback_data="time_Вечір")],
        [InlineKeyboardButton("🕐 Будь-коли", callback_data="time_any")]
    ]
    await update_or_query.message.reply_text("⏰ Коли ви доступні:",
                                             reply_markup=InlineKeyboardMarkup(keyboard))

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
        "🌸🌼💮🌺🌸💐🌷🌻🌸\n"
        "<b>Ви зареєстровані як виконавець!</b>\n"
        "Тепер можете переглянути <b>/nearby</b> замовлення поруч 🛠️\n"
        "🌸💐✨ Дякуємо, що з нами! ✨🌸💮",
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

async def take_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg_text = update.message.text
    if not msg_text.startswith("/take_"):
        return

    order_id = int(msg_text.split("_")[1])

    with open("orders.json", "r", encoding="utf-8") as f:
        orders = json.load(f)

    for order in orders:
        if order["id"] == order_id and order["status"] == "нове":
            order["status"] = "взято"
            order["assigned_to"] = user_id
            break

    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)

    await update.message.reply_text("✅ Ви взяли це замовлення! Успіхів 🙌")

async def service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "toggle_" in query.data:
        index = int(query.data.split("_")[1])
        service = SERVICE_OPTIONS[index]
        selected = context.user_data.get("selected_services", [])

        if service in selected:
            selected.remove(service)
        else:
            selected.append(service)

        context.user_data["selected_services"] = selected
        keyboard = build_service_keyboard(selected)
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "done":
        selected = context.user_data.get("selected_services", [])
        if not selected:
            await query.answer("❗ Виберіть хоча б одну опцію", show_alert=True)
            return

        context.user_data["services"] = selected
        await query.edit_message_text(
            f"📝 Ви обрали: {', '.join(selected)}\n\nВсе правильно?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Так, зберегти", callback_data="save_services")],
                [InlineKeyboardButton("🔄 Змінити", callback_data="change_services")]
            ])
        )

    elif query.data == "change_services":
        keyboard = build_service_keyboard(context.user_data["selected_services"])
        await query.edit_message_text(
            "📌 Оберіть, що ви можете робити (можна кілька):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "save_services":
        await query.edit_message_text("✅ Послуги збережені.")
        await ask_area(query, context)

    elif query.data.startswith("area_") and query.data not in ["area_confirm", "area_change"]:
        area = query.data.split("_", 1)[1]
        context.user_data["area"] = area if area != "any" else "будь-який"
        await query.edit_message_text(
            f"📍 Район обрано: {context.user_data['area']}\n\nВсе вірно?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Так", callback_data="area_confirm")],
                [InlineKeyboardButton("🔄 Змінити", callback_data="area_change")]
            ])
        )

    elif query.data == "area_change":
        await ask_area(query, context)

    elif query.data == "area_confirm":
        await query.edit_message_text("✅ Район підтверджено.")
        await ask_location(query, context)

    elif query.data.startswith("time_"):
        time = query.data.split("_", 1)[1]
        context.user_data["availability"] = time if time != "any" else "будь-коли"
        readable = context.user_data["availability"]
        await query.edit_message_text(
            f"🕐 Доступність: {readable}\n\nВсе правильно?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Так", callback_data="time_confirm")],
                [InlineKeyboardButton("🔄 Змінити", callback_data="time_change")]
            ])
        )

    elif query.data == "time_change":
        await ask_availability(query, context)

    elif query.data == "time_confirm":
        profile = {
            "id": generate_worker_id(),
            "user_id": query.from_user.id,
            "name": context.user_data['name'],
            "services": context.user_data['services'],
            "area": context.user_data['area'],
            "availability": context.user_data['availability'],
            "location": context.user_data.get("location", {}),
            "rating": 0
        }
        save_worker(profile)
        await query.edit_message_text("🌸 Ви зареєстровані як виконавець! Дякуємо! 🌼")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    register_conversation = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(register_conversation)
    app.add_handler(CallbackQueryHandler(service_callback))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(CommandHandler("nearby", nearby_orders))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/take_"), take_order))

    print("🤖 EasyMe бот запущено!")
    app.run_polling()



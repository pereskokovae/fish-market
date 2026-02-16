import os
import io
import requests
import re

from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    CallbackQueryHandler, Filters
    )

from store_api import (
    fetch_product_by_id, fetch_products, get_title,
    get_description, get_price, get_picture_url,
    add_item_to_cart, get_cart_by_telegram_id,
    remove_item_from_cart, upsert_client_email
    )
from create_keyboards import (
    build_products_menu_keyboard,
    build_product_details_keyboard,
    build_empty_cart_keyboard,
    build_cart_keyboard
    )
from redis_storage import get_state, get_database_connection, set_state

from dotenv import load_dotenv


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def send_products_menu(bot, chat_id: int, base_url: str, token: str):
    payload = fetch_products(base_url, token)
    items = payload.get("data") or []

    products_for_menu = []
    for item in items:
        product_id = item.get("id")
        title = get_title(item)

        if not title or product_id is None:
            continue
        products_for_menu.append({"id": str(product_id), "title": title})

    reply_markup = build_products_menu_keyboard(products_for_menu)

    bot.send_message(
        chat_id=chat_id,
        text="Пожалуйста выберите:",
        reply_markup=reply_markup,
    )


def send_product_details(bot, chat_id: int, base_url: str, token: str, product_id: str):
    payload = fetch_product_by_id(base_url, token, product_id)
    data = payload.get("data")

    if isinstance(data, list):
        item = data[0] if data else {}
    else:
        item = data or {}

    title = get_title(item) or "Без названия"
    description = get_description(item)
    price = get_price(item)

    header = f"{title} ({price} руб.за кг)" if price is not None else title
    text = f"{header}\n\n{description}".strip()

    reply_markup = build_product_details_keyboard(product_id)

    picture_url = get_picture_url(base_url, item)

    if picture_url:
        image_response = requests.get(picture_url, timeout=5)
        image_response.raise_for_status()

        bot.send_photo(
            chat_id=chat_id,
            photo=io.BytesIO(image_response.content),
            caption=text,
            reply_markup=reply_markup
        )
    else:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )


def start(update, context):
    base_url = context.bot_data["STRAPI_URL"]
    token = context.bot_data["STRAPI_TOKEN"]
    chat_id = update.effective_chat.id

    send_products_menu(context.bot, chat_id, base_url, token)
    return "HANDLE_MENU"


def handle_menu(update, context):
    query = update.callback_query
    query.answer()

    base_url = context.bot_data["STRAPI_URL"]
    token = context.bot_data["STRAPI_TOKEN"]
    chat_id = query.message.chat_id

    if query.data == "back":
        send_products_menu(context.bot, chat_id, base_url, token)
        return "HANDLE_MENU"

    if query.data == "cart":
        try:
            query.message.delete()
        except Exception:
            pass
        render_cart(context.bot, chat_id, base_url, token)
        return "HANDLE_CART"

    context.bot.delete_message(
        chat_id=chat_id,
        message_id=query.message.message_id
    )

    send_product_details(context.bot, chat_id, base_url, token, query.data)
    return "HANDLE_DESCRIPTION"


def handle_description(update, context):
    query = update.callback_query
    query.answer()

    base_url = context.bot_data["STRAPI_URL"]
    token = context.bot_data["STRAPI_TOKEN"]
    chat_id = query.message.chat_id

    if query.data == "back":
        query.message.delete()

        send_products_menu(context.bot, chat_id, base_url, token)
        return "HANDLE_MENU"

    if query.data.startswith("add_to_cart:"):
        product_id = int(query.data.split(":", 1)[1])
        add_item_to_cart(
            base_url,
            token,
            telegram_id=chat_id,
            product_id=product_id,
            quantity=1
        )
        query.message.reply_text("Добавлено в корзину")
        return "HANDLE_DESCRIPTION"

    if query.data == "cart":
        try:
            query.message.delete()
        except Exception:
            pass
        render_cart(context.bot, chat_id, base_url, token)
        return "HANDLE_CART"

    return "HANDLE_DESCRIPTION"


def handle_users_reply(update, context):
    db = get_database_connection()
    chat_id = update.effective_chat.id

    if update.message and update.message.text == "/start":
        state = "START"
    else:
        state = get_state(db, chat_id)

    states = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "HANDLE_DESCRIPTION": handle_description,
        "HANDLE_CART": handle_cart,
        "WAITING_EMAIL": handle_waiting_email
    }

    next_state = states[state](update, context)
    set_state(db, chat_id, next_state)


def render_cart(bot, chat_id: int, base_url: str, token: str):
    cart = get_cart_by_telegram_id(base_url, token, chat_id)

    if not cart or not (cart.get("items") or []):
        bot.send_message(
            chat_id=chat_id,
            text="Корзина пуста.",
            reply_markup=build_empty_cart_keyboard()
        )
        return

    items = cart["items"]

    lines = ["Ваша корзина:\n"]
    total = 0

    for it in items:
        product = it.get("product") or {}
        title = product.get("title", "Без названия")
        price = int(product.get("price") or 0)
        quantity = int(it.get("quantity") or 0)

        subtotal = price * quantity
        total += subtotal
        lines.append(f"{title} — {quantity} шт. × {price} = {subtotal}")

    lines.append(f"\nИтого: {total} руб.")

    reply_markup = build_cart_keyboard(items)

    bot.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        reply_markup=reply_markup
    )


def handle_cart(update, context):
    query = update.callback_query
    query.answer()

    base_url = context.bot_data["STRAPI_URL"]
    token = context.bot_data["STRAPI_TOKEN"]
    chat_id = query.message.chat_id

    try:
        query.message.delete()
    except Exception:
        pass

    if query.data == "back_to_menu":
        send_products_menu(context.bot, chat_id, base_url, token)
        return "HANDLE_MENU"

    if query.data.startswith("remove:"):
        product_id = int(query.data.split(":", 1)[1])
        remove_item_from_cart(base_url, token, chat_id, product_id)
        render_cart(context.bot, chat_id, base_url, token)
        return "HANDLE_CART"

    if query.data == "pay":
        context.bot.send_message(
            chat_id=chat_id,
            text="Напишите, пожалуйста, свою почту для оформления заказа"
        )
        return "WAITING_EMAIL"

    render_cart(context.bot, chat_id, base_url, token)
    return "HANDLE_CART"


def handle_waiting_email(update, context):
    chat_id = update.effective_chat.id

    if not update.message or not update.message.text:
        context.bot.send_message(chat_id=chat_id, text="Пришлите почту текстом")
        return "WAITING_EMAIL"

    email = update.message.text.strip()

    if not EMAIL_RE.match(email):
        context.bot.send_message(
            chat_id=chat_id,
            text="Похоже, это не email. Пример: name@gmail.com\nПопробуй ещё раз:"
        )
        return "WAITING_EMAIL"

    base_url = context.bot_data["STRAPI_URL"]
    token = context.bot_data["STRAPI_TOKEN"]

    upsert_client_email(base_url, token, telegram_id=chat_id, email=email)

    context.bot.send_message(chat_id=chat_id, text="Почта сохранена!")
    send_products_menu(context.bot, chat_id, base_url, token)
    return "HANDLE_MENU"


if __name__ == "__main__":
    load_dotenv()

    tg_token = os.getenv("TG_TOKEN")
    strapi_url = os.getenv("STRAPI_URL", default="http://localhost:1337")
    strapi_token = os.getenv("STRAPI_TOKEN")

    updater = Updater(tg_token)
    dp = updater.dispatcher

    dp.bot_data["STRAPI_URL"] = strapi_url
    dp.bot_data["STRAPI_TOKEN"] = strapi_token

    dp.add_handler(CommandHandler("start", handle_users_reply))
    dp.add_handler(CallbackQueryHandler(handle_users_reply))
    dp.add_handler(MessageHandler(Filters.text, handle_users_reply))

    updater.start_polling()
    updater.idle()

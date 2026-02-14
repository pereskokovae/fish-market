from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_products_menu_keyboard(products_for_menu: list) -> InlineKeyboardMarkup:
    keyboard = []
    for product in products_for_menu:
        keyboard.append([InlineKeyboardButton(product["title"], callback_data=product["id"])])
    keyboard.append([InlineKeyboardButton("Моя корзина", callback_data="cart")])
    return InlineKeyboardMarkup(keyboard)


def build_product_details_keyboard(product_id: str):
    keyboard = [
        [InlineKeyboardButton(
            "Добавить в корзину",
            callback_data=f"add_to_cart:{product_id}"
            )],
        [InlineKeyboardButton("Назад к списку", callback_data="back")],
        [InlineKeyboardButton("Моя корзина", callback_data="cart")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_empty_cart_keyboard():
    keyboard = [[InlineKeyboardButton("В меню", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(keyboard)


def build_cart_keyboard(cart_items: list):
    keyboard = []

    for cart_item in cart_items:
        product = cart_item.get("product") or {}
        title = product.get("title", "Без названия")
        product_id = product.get("id")

        if product_id is None:
            continue

        keyboard.append([InlineKeyboardButton(
            f"Убрать {title}", callback_data=f"remove:{product_id}"
            )])

    keyboard.append([InlineKeyboardButton(
        "В меню",
        callback_data="back_to_menu"
        )])
    keyboard.append([InlineKeyboardButton("Оплатить", callback_data="pay")])
    return InlineKeyboardMarkup(keyboard)

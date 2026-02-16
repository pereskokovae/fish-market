import requests


def _headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def fetch_products(base_url: str, token: str):
    url = f"{base_url.rstrip('/')}/api/products"
    response = requests.get(url, headers=_headers(token), timeout=5)
    response.raise_for_status()
    return response.json()


def fetch_product_by_id(base_url: str, token: str, product_id: str):
    base = base_url.rstrip("/")
    params = {"populate": "picture"}
    url = f"{base}/api/products/{product_id}"
    response = requests.get(url, headers=_headers(token), params=params, timeout=5)

    if response.status_code == 404:
        url = f"{base}/api/products"
        params = {"filters[id][$eq]": product_id, "populate": "picture"}
        response = requests.get(url, params=params, headers=_headers(token), timeout=5)
        response.raise_for_status()
        return response.json()

    response.raise_for_status()
    return response.json()


def get_title(item: dict):
    title = item.get("title")
    return str(title).strip()


def get_description(item: dict) -> str:
    description = item.get("description")
    return str(description).strip()


def get_price(item: dict):
    price = item.get("price")
    return price


def get_picture_url(base_url: str, item: dict):
    base = base_url.rstrip("/")

    picture = item.get("picture")
    if not picture:
        return None

    url = picture.get("url")
    if not url:
        return None

    return f"{base}{url}"


def create_cart(base_url: str, token: str, telegram_id: int):
    url = f"{base_url.rstrip('/')}/api/carts"
    payload = {"data": {"telegram_id": str(telegram_id)}}
    response = requests.post(url, json=payload, headers=_headers(token), timeout=15)
    response.raise_for_status()
    return response.json()["data"]


def get_cart_by_telegram_id(base_url: str, token: str, telegram_id: int):
    url = f"{base_url.rstrip('/')}/api/carts"
    params = {
        "filters[telegram_id][$eq]": str(telegram_id),
        "populate[items][populate]": "product",
    }
    response = requests.get(url, headers=_headers(token), params=params, timeout=15)
    response.raise_for_status()
    clients = response.json().get("data") or []
    return clients[0] if clients else None


def add_item_to_cart(base_url: str, token: str, telegram_id: int, product_id: int, quantity: int = 1):
    cart = get_cart_by_telegram_id(base_url, token, telegram_id)
    if not cart:
        cart = create_cart(base_url, token, telegram_id)

    cart_document_id = cart["documentId"]    

    raw_items = cart.get("items")
    if raw_items is None:
        raw_items = (cart.get("attributes") or {}).get("items") or []
    else:
        raw_items = raw_items or []

    items = []
    for it in raw_items:
        pid = it.get("product")

        if isinstance(pid, dict):
            pid = pid.get("id") or (pid.get("data") or {}).get("id")

        items.append({
            "product": int(pid),
            "quantity": int(it.get("quantity") or 0),
        })

    for it in items:
        if it["product"] == int(product_id):
            it["quantity"] += int(quantity)
            break
    else:
        items.append({"product": int(product_id), "quantity": int(quantity)})

    url = f"{base_url.rstrip('/')}/api/carts/{cart_document_id}"
    payload = {"data": {"items": items}}

    response = requests.put(url, headers=_headers(token), json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def remove_item_from_cart(base_url: str, token: str, telegram_id: int, product_id: int):
    cart = get_cart_by_telegram_id(base_url, token, telegram_id)
    if not cart:
        return None

    cart_doc_id = cart["documentId"]

    raw_items = cart.get("items")
    if raw_items is None:
        raw_items = (cart.get("attributes") or {}).get("items") or []
    else:
        raw_items = raw_items or []

    new_items = []
    for it in raw_items:
        pid = it.get("product")

        if isinstance(pid, dict):
            pid = pid.get("id") or (pid.get("data") or {}).get("id")

        if int(pid) != int(product_id):
            new_items.append({
                "product": int(pid),        
                "quantity": int(it.get("quantity") or 0),
            })
    url = f"{base_url.rstrip('/')}/api/carts/{cart_doc_id}"
    payload = {"data": {"items": new_items}}
    response = requests.put(url, headers=_headers(token), json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def get_client_by_telegram_id(base_url: str, token: str, telegram_id: int):
    url = f"{base_url.rstrip('/')}/api/clients"
    params = {"filters[telegram_id][$eq]": str(telegram_id)}
    response = requests.get(url, headers=_headers(token), params=params, timeout=15)
    response.raise_for_status()
    data = response.json().get("data") or []
    return data[0] if data else None


def create_client(base_url: str, token: str, telegram_id: int, email: str):
    url = f"{base_url.rstrip('/')}/api/clients"
    payload = {"data": {"telegram_id": str(telegram_id), "email": email}}
    response = requests.post(url, headers=_headers(token), json=payload, timeout=15)
    response.raise_for_status()
    return response.json()["data"]


def upsert_client_email(base_url: str, token: str, telegram_id: int, email: str):
    client = get_client_by_telegram_id(base_url, token, telegram_id)
    if not client:
        return create_client(base_url, token, telegram_id, email)

    doc_id = client.get("documentId")
    if not doc_id:
        client_id = client["id"]
        url = f"{base_url.rstrip('/')}/api/clients/{client_id}"
    else:
        url = f"{base_url.rstrip('/')}/api/clients/{doc_id}"

    payload = {"data": {"email": email}}
    response = requests.put(url, headers=_headers(token), json=payload, timeout=15)
    response.raise_for_status()
    return response.json()["data"]

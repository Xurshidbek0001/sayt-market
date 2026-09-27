import json
import os

ORDERS_FILE = "orders.json"


def _load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []

    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)


def save_order(order):
    orders = _load_orders()

    order_id = len(orders) + 1
    order["order_id"] = order_id

    orders.append(order)
    _save_orders(orders)

    return order_id


def get_user_orders(user_id):
    orders = _load_orders()

    return [
        order
        for order in orders
        if order.get("user_id") == user_id
  ]

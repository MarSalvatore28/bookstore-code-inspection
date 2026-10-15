"""Order processing logic."""
import sqlite3

import database
import auth

TAX = 0.15
SEPARATOR = "=============================="
_order_log = []
COUPON_RATES = {"WELCOME10": 0.9, "BLACKFRIDAY": 0.5}
SHIPPING_COSTS = {"express": 10, "standard": 3}


def process_order(token, items, coupon=None, shipping="standard", log=None):
    if log is None:
        log = _order_log
    username = auth.sessions.get(token)
    if username is None:
        print("Invalid session")
        return None
    if not items:
        print("Empty order")
        return None
    total = sum(_item_cost(item) for item in items)
    total = _apply_coupon(total, coupon, token)
    total = total + SHIPPING_COSTS.get(shipping, 0)
    total = total + total * TAX
    order_id = len(log) + 1
    database.save_order(order_id, username, total, "PENDING")
    log.append(order_id)
    return round(total, 2)


def _item_cost(item):
    book = database.get_book(item["book_id"])
    if not book:
        print("Book not found")
        return 0
    if item["qty"] > book[3]:
        if book[3] > 0:
            print("Only " + str(book[3]) + " units available for " + book[1])
        else:
            print("Book out of stock: " + book[1])
        return 0
    if item["qty"] <= 0:
        print("Invalid quantity")
        return 0
    database.update_stock(book[0], book[3] - item["qty"])
    return book[2] * item["qty"]


def _apply_coupon(total, coupon, token):
    if coupon == "STAFF":
        return total * 0.7 if auth.is_admin(token) else total
    return total * COUPON_RATES.get(coupon, 1)


def print_invoice(username, items):
    _print_document("BOOKSTORE INVOICE", username, items)
    print(SEPARATOR)


def print_quote(username, items):
    _print_document("BOOKSTORE QUOTE", username, items)
    print("This quote is valid for 7 days.")
    print(SEPARATOR)


def _print_document(title, username, items):
    print(SEPARATOR)
    print(title)
    print("Customer: " + username)
    print(SEPARATOR)
    subtotal = 0
    for item in items:
        book = database.get_book(item["book_id"])
        line_total = book[2] * item["qty"]
        subtotal = subtotal + line_total
        print(book[1] + " x" + str(item["qty"]) + " = " + str(line_total))
    tax = subtotal * TAX
    print("Subtotal: " + str(round(subtotal, 2)))
    print("Tax: " + str(round(tax, 2)))
    print("Total: " + str(round(subtotal + tax, 2)))


def cancel_order(order_id):
    try:
        conn = database.get_connection()
        conn.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = ?", (order_id,))
        conn.commit()
    except sqlite3.Error as error:
        print("Could not cancel order: " + str(error))

"""Authentication and session handling."""
import hashlib
import hmac
import secrets

import database

HASH_ITERATIONS = 600_000
sessions = {}


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), HASH_ITERATIONS
    ).hex()
    return salt + "$" + digest


def verify_password(password, stored_hash):
    salt = stored_hash.split("$", 1)[0]
    return hmac.compare_digest(hash_password(password, salt), stored_hash)


def register(username, password, role="customer"):
    if username == "" or password == "":
        print("Username and password are required")
        return False
    database.add_user(username, hash_password(password), role)
    return True


def login(username, password):
    user = database.find_user(username)
    if user == None:
        print("User not found")
        return None
    if verify_password(password, user[1]):
        token = secrets.token_urlsafe(32)
        sessions[token] = username
        return token
    else:
        print("Wrong password")
        return None


def is_admin(token):
    username = sessions.get(token)
    user = database.find_user(username)
    if user[2] == "admin":
        return True
    else:
        return False


def apply_discount_rule(rule, total):
    # rule comes from the admin panel, e.g. "total * 0.9"
    return eval(rule)

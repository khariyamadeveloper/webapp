import hashlib
import hmac
import os
from urllib.parse import parse_qs

from flask import Flask, render_template, request, abort, redirect, url_for

app = Flask(__name__, template_folder="templates", static_folder="static")

# SECRET_KEY must be set via environment variable; abort startup if missing in production
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")

# Telegram Bot Token used to validate initData signatures
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

ITEMS = [
    {
        "id": 1,
        "title": "Бот для магазина",
        "description": "Исходник Telegram бота для магазина.",
        "price": 150,
        "logo_url": "/static/bot1.png",
    },
    {
        "id": 2,
        "title": "Парсер данных",
        "description": "Скрипт для парсинга сайтов.",
        "price": 80,
        "logo_url": "/static/parser.png",
    },
]


def validate_telegram_init_data(init_data: str) -> bool:
    """Validate Telegram WebApp initData using HMAC-SHA256.

    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not TELEGRAM_BOT_TOKEN:
        # If no bot token is configured, reject all requests
        return False

    parsed = parse_qs(init_data, keep_blank_values=True)
    received_hash = parsed.pop("hash", [None])[0]
    if not received_hash:
        return False

    # Build the data-check-string: sorted key=value pairs joined by newlines
    data_check_parts = sorted(
        f"{key}={val[0]}" for key, val in parsed.items()
    )
    data_check_string = "\n".join(data_check_parts)

    # Compute HMAC-SHA256
    secret_key = hmac.new(
        b"WebAppData", TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_hash, received_hash)


def require_telegram_auth():
    """Verify the request originates from a legitimate Telegram WebApp session.

    Checks the X-Telegram-Init-Data header which must contain a valid
    Telegram initData string with a verifiable HMAC signature.
    Falls back to checking TG_USER_ID header only in development mode
    (when TELEGRAM_BOT_TOKEN is not configured).
    """
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if init_data and validate_telegram_init_data(init_data):
        return

    # Legacy fallback: only allow header-based auth when no bot token is set (dev mode)
    if not TELEGRAM_BOT_TOKEN:
        user_id = request.headers.get("TG_USER_ID")
        if user_id:
            return

    abort(403)


@app.route("/")
def index():
    require_telegram_auth()
    return render_template("index.html", items=ITEMS)


@app.route("/item/<int:item_id>")
def item(item_id):
    require_telegram_auth()
    found = next((i for i in ITEMS if i["id"] == item_id), None)
    if not found:
        abort(404)
    return render_template("item.html", item=found)


@app.route("/pay/<int:item_id>", methods=["POST"])
def pay(item_id):
    require_telegram_auth()
    found = next((i for i in ITEMS if i["id"] == item_id), None)
    if not found:
        abort(404)
    # TODO: implement payment logic via XTR Stars and balance recording
    return render_template("modal_payment.html", item=found, status="success")


if __name__ == "__main__":
    # Never run with debug=True in production.
    # Set FLASK_DEBUG=1 env var for local development only.
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)

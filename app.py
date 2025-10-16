import os
from flask import Flask, render_template, request, abort, redirect, url_for

app = Flask(__name__, template_folder="templates", static_folder="static")

# Пример товаров
ITEMS = [
    {
        "id": 1,
        "title": "Бот для магазина",
        "description": "Исходник Telegram бота для магазина.",
        "price": 150,
        "logo_url": "/static/bot1.png"
    },
    {
        "id": 2,
        "title": "Парсер данных",
        "description": "Скрипт для парсинга сайтов.",
        "price": 80,
        "logo_url": "/static/parser.png"
    }
    # Добавь свои исходники…
]

def require_telegram_auth():
    user_id = request.headers.get("TG_USER_ID")
    if not user_id:
        abort(403)

@app.route("/")
def index():
    require_telegram_auth()
    return render_template("index.html", items=ITEMS)

@app.route("/item/<int:item_id>")
def item(item_id):
    require_telegram_auth()
    item = next((i for i in ITEMS if i["id"] == item_id), None)
    if not item:
        abort(404)
    return render_template("item.html", item=item)

@app.route("/pay/<int:item_id>", methods=["POST"])
def pay(item_id):
    require_telegram_auth()
    item = next((i for i in ITEMS if i["id"] == item_id), None)
    if not item:
        abort(404)
    # Тут должна быть логика оплаты через XTR Stars и запись на баланс
    return render_template("modal_payment.html", item=item, status="success")

if __name__ == "__main__":
    app.run(debug=True)

import os
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
from src.finance_tracker import PersonalFinanceTracker, TransactionType

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DATA_DIR, "finance.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "finance-tracker-secret-key-change-in-prod")

tracker = PersonalFinanceTracker(db_path=DB_PATH)


@app.route("/")
def index():
    """Главная страница со списком операций и сводкой."""
    summary = tracker.get_summary()
    transactions = tracker.get_transactions()
    categories_expense = [
        "Продукты", "Транспорт", "Жилье", "Кафе", "Развлечения", "Здоровье", "Одежда", "Другое"
    ]
    categories_income = [
        "Зарплата", "Аванс", "Фриланс", "Премия", "Инвестиции", "Другое"
    ]
    return render_template(
        "index.html",
        summary=summary,
        transactions=transactions,
        categories_expense=categories_expense,
        categories_income=categories_income
    )


@app.route("/add", methods=["POST"])
def add_transaction():
    """Добавление новой операции (доход или расход)."""
    try:
        raw_amount = request.form.get("amount", "").strip().replace(",", ".")
        amount = float(raw_amount)
        trans_type_val = request.form.get("type", "expense").strip()
        category = request.form.get("category", "").strip()
        custom_category = request.form.get("custom_category", "").strip()
        description = request.form.get("description", "").strip()

        if category == "Другое" and custom_category:
            category = custom_category

        if not category:
            flash("Укажите категорию операции.", "error")
            return redirect(url_for("index"))

        trans_type = TransactionType(trans_type_val)
        tracker.add_transaction(amount=amount, trans_type=trans_type, category=category, description=description)
        flash("Операция успешно добавлена.", "success")
    except ValueError as e:
        flash(f"Ошибка валидации: {str(e)}", "error")
    except Exception as e:
        flash(f"Ошибка: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/delete/<int:trans_id>", methods=["POST"])
def delete_transaction(trans_id: int):
    """Удаление операции по идентификатору."""
    if tracker.delete_transaction(trans_id):
        flash(f"Операция #{trans_id} удалена.", "info")
    else:
        flash(f"Операция #{trans_id} не найдена.", "error")
    return redirect(url_for("index"))


@app.route("/api/summary", methods=["GET"])
def api_summary():
    """API получения финансовой сводки."""
    return jsonify(tracker.get_summary())


@app.route("/health", methods=["GET"])
def health_check():
    """Эндпоинт проверки работоспособности сервиса для CI/CD."""
    return jsonify({
        "status": "healthy",
        "service": "personal-finance-calculator",
        "version": "1.0.0"
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

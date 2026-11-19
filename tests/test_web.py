import pytest
from src.app import app, tracker


@pytest.fixture
def client():
    """Тестовый клиент Flask с очищенным трекером."""
    app.config["TESTING"] = True
    tracker.clear()
    with app.test_client() as client:
        yield client
    tracker.clear()


def test_health_check(client):
    """Проверка health-check эндпоинта (критично для CI/CD)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "personal-finance-calculator"


def test_index_page_empty(client):
    """Главная страница возвращает 200 OK при пустой базе."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Учет личных финансов".encode("utf-8") in response.data


def test_add_income_via_form(client):
    """Добавление дохода через HTML форму."""
    response = client.post(
        "/add",
        data={
            "amount": "25000",
            "type": "income",
            "category": "Зарплата",
            "description": "Бонус за проект"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert tracker.get_balance() == 25000.0
    assert len(tracker.get_transactions()) == 1


def test_add_expense_via_form(client):
    """Добавление расхода через HTML форму."""
    response = client.post(
        "/add",
        data={
            "amount": "1200.50",
            "type": "expense",
            "category": "Продукты",
            "description": "Покупка еды"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert tracker.get_total_expenses() == 1200.50
    assert tracker.get_balance() == -1200.50


def test_add_invalid_amount(client):
    """Попытка отправить отрицательную сумму должна вызывать ошибку валидации."""
    response = client.post(
        "/add",
        data={
            "amount": "-500",
            "type": "expense",
            "category": "Продукты",
            "description": ""
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Ошибка валидации".encode("utf-8") in response.data
    assert len(tracker.get_transactions()) == 0


def test_delete_transaction(client):
    """Удаление транзакции через POST /delete/<id>."""
    t = tracker.add_income(1000, "Премия")
    assert tracker.get_balance() == 1000.0

    response = client.post(f"/delete/{t.id}", follow_redirects=True)
    assert response.status_code == 200
    assert tracker.get_balance() == 0.0


def test_api_summary(client):
    """Проверка JSON API /api/summary."""
    tracker.add_income(5000, "Зарплата")
    tracker.add_expense(2000, "Одежда")

    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.get_json()
    assert data["balance"] == 3000.0
    assert data["total_income"] == 5000.0
    assert data["total_expenses"] == 2000.0
    assert data["expenses_by_category"]["Одежда"] == 2000.0

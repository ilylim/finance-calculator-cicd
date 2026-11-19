import os
import tempfile
import pytest
from src.finance_tracker import PersonalFinanceTracker, TransactionType


class TestPersonalFinanceTracker:
    @pytest.fixture
    def tracker(self):
        """Фикстура для изолированного экземпляра трекера в памяти."""
        return PersonalFinanceTracker()

    def test_initial_state(self, tracker):
        """Проверка начального состояния трекера."""
        assert tracker.get_balance() == 0.0
        assert tracker.get_total_income() == 0.0
        assert tracker.get_total_expenses() == 0.0
        assert len(tracker.get_transactions()) == 0

    def test_add_income(self, tracker):
        """Проверка добавления дохода."""
        tx = tracker.add_income(50000.0, "Зарплата", "Основная работа")
        assert tx.id == 1
        assert tx.amount == 50000.0
        assert tx.type == TransactionType.INCOME
        assert tx.category == "Зарплата"
        assert tracker.get_total_income() == 50000.0
        assert tracker.get_balance() == 50000.0

    def test_add_expense(self, tracker):
        """Проверка добавления расхода."""
        tx = tracker.add_expense(1500.50, "Продукты", "Супермаркет")
        assert tx.id == 1
        assert tx.amount == 1500.50
        assert tx.type == TransactionType.EXPENSE
        assert tx.category == "Продукты"
        assert tracker.get_total_expenses() == 1500.50
        assert tracker.get_balance() == -1500.50

    def test_balance_calculation(self, tracker):
        """Проверка корректного расчета итогового баланса."""
        tracker.add_income(100000.0, "Зарплата")
        tracker.add_income(15000.0, "Фриланс")
        tracker.add_expense(30000.0, "Аренда жилья")
        tracker.add_expense(12000.0, "Еда")

        assert tracker.get_total_income() == 115000.0
        assert tracker.get_total_expenses() == 42000.0
        assert tracker.get_balance() == 73000.0

    @pytest.mark.parametrize("invalid_amount", [0, -100, -0.01])
    def test_invalid_amount_raises_error(self, tracker, invalid_amount):
        """Сумма операции должна быть строго положительной."""
        with pytest.raises(ValueError, match="строго положительным"):
            tracker.add_income(invalid_amount, "Тест")

    @pytest.mark.parametrize("invalid_category", ["", "   ", None])
    def test_empty_category_raises_error(self, tracker, invalid_category):
        """Категория не должна быть пустой строкой."""
        with pytest.raises((ValueError, AttributeError)):
            tracker.add_expense(500, invalid_category)

    def test_delete_transaction(self, tracker):
        """Проверка удаления транзакции."""
        tracker.add_income(1000, "Премия")
        t2 = tracker.add_expense(300, "Кафе")

        assert len(tracker.get_transactions()) == 2
        assert tracker.get_balance() == 700.0

        # Удаляем расход
        deleted = tracker.delete_transaction(t2.id)
        assert deleted is True
        assert len(tracker.get_transactions()) == 1
        assert tracker.get_balance() == 1000.0

        # Попытка удалить несуществующую транзакцию
        assert tracker.delete_transaction(999) is False

    def test_category_breakdown(self, tracker):
        """Проверка аналитики по категориям трат."""
        tracker.add_expense(2000, "Продукты")
        tracker.add_expense(1500, "Продукты")
        tracker.add_expense(800, "Транспорт")
        tracker.add_income(5000, "Зарплата")

        breakdown = tracker.get_category_breakdown(TransactionType.EXPENSE)
        assert breakdown["Продукты"] == 3500.0
        assert breakdown["Транспорт"] == 800.0
        assert "Зарплата" not in breakdown

    def test_filter_transactions(self, tracker):
        """Фильтрация операций по типу и категории."""
        tracker.add_income(5000, "Зарплата")
        tracker.add_income(2000, "Подарок")
        tracker.add_expense(1000, "Продукты")

        incomes = tracker.get_transactions(trans_type=TransactionType.INCOME)
        assert len(incomes) == 2

        expenses = tracker.get_transactions(trans_type=TransactionType.EXPENSE)
        assert len(expenses) == 1

        salary = tracker.get_transactions(category="Зарплата")
        assert len(salary) == 1
        assert salary[0].amount == 5000

    def test_db_persistence(self):
        """Проверка сохранения в базу данных и чтения между экземплярами."""
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            tracker1 = PersonalFinanceTracker(db_path=tmp_path)
            tracker1.add_income(12000, "Зарплата", "Аванс")
            tracker1.add_expense(3500, "ЖКХ", "Свет и вода")

            # Создаем второй трекер, указывая на тот же файл БД
            tracker2 = PersonalFinanceTracker(db_path=tmp_path)
            assert len(tracker2.get_transactions()) == 2
            assert tracker2.get_balance() == 8500.0

            # Добавляем третью операцию во втором трекере
            tracker2.add_expense(500, "Интернет")

            # Первый трекер сразу же видит изменения из БД
            assert tracker1.get_balance() == 8000.0
            assert len(tracker1.get_transactions()) == 3
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

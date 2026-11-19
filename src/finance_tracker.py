import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TransactionType(str, Enum):
    """Тип финансовой транзакции."""
    INCOME = "income"
    EXPENSE = "expense"


class Transaction:
    """Модель отдельной финансовой операции."""

    def __init__(
        self,
        trans_id: int,
        amount: float,
        trans_type: TransactionType,
        category: str,
        description: str = "",
        created_at: Optional[str] = None
    ):
        if amount <= 0:
            raise ValueError("Сумма операции должна быть строго положительным числом.")

        if not category or not category.strip():
            raise ValueError("Категория операции не может быть пустой.")

        self.id = trans_id
        self.amount = round(float(amount), 2)
        self.type = trans_type if isinstance(trans_type, TransactionType) else TransactionType(trans_type)
        self.category = category.strip()
        self.description = description.strip() if description else ""
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "amount": self.amount,
            "type": self.type.value,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Создание экземпляра из словаря."""
        return cls(
            trans_id=data["id"],
            amount=data["amount"],
            trans_type=TransactionType(data["type"]),
            category=data["category"],
            description=data.get("description", ""),
            created_at=data.get("created_at")
        )


class PersonalFinanceTracker:
    """
    Класс для управления личными финансами:
    учет доходов, расходов, расчет баланса и аналитики по категориям.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self._transactions: List[Transaction] = []
        self._next_id: int = 1

        if self.storage_path and os.path.exists(self.storage_path):
            self.load_from_file(self.storage_path)

    def add_transaction(
        self,
        amount: float,
        trans_type: TransactionType,
        category: str,
        description: str = "",
        created_at: Optional[str] = None
    ) -> Transaction:
        """Добавить новую операцию."""
        transaction = Transaction(
            trans_id=self._next_id,
            amount=amount,
            trans_type=trans_type,
            category=category,
            description=description,
            created_at=created_at
        )
        self._transactions.append(transaction)
        self._next_id += 1

        if self.storage_path:
            self.save_to_file(self.storage_path)

        return transaction

    def add_income(self, amount: float, category: str, description: str = "") -> Transaction:
        """Удобный метод для добавления дохода."""
        return self.add_transaction(amount, TransactionType.INCOME, category, description)

    def add_expense(self, amount: float, category: str, description: str = "") -> Transaction:
        """Удобный метод для добавления расхода."""
        return self.add_transaction(amount, TransactionType.EXPENSE, category, description)

    def delete_transaction(self, trans_id: int) -> bool:
        """Удалить операцию по идентификатору."""
        initial_len = len(self._transactions)
        self._transactions = [t for t in self._transactions if t.id != trans_id]
        deleted = len(self._transactions) < initial_len

        if deleted and self.storage_path:
            self.save_to_file(self.storage_path)

        return deleted

    def get_transactions(
        self,
        trans_type: Optional[TransactionType] = None,
        category: Optional[str] = None
    ) -> List[Transaction]:
        """Получить список операций с возможностью фильтрации."""
        result = self._transactions
        if trans_type:
            result = [t for t in result if t.type == trans_type]
        if category:
            result = [t for t in result if t.category.lower() == category.lower()]
        return list(reversed(result))  # Сначала самые свежие

    def get_total_income(self) -> float:
        """Рассчитать общую сумму всех доходов."""
        total = sum(t.amount for t in self._transactions if t.type == TransactionType.INCOME)
        return round(total, 2)

    def get_total_expenses(self) -> float:
        """Рассчитать общую сумму всех расходов."""
        total = sum(t.amount for t in self._transactions if t.type == TransactionType.EXPENSE)
        return round(total, 2)

    def get_balance(self) -> float:
        """Рассчитать текущий баланс (доходы - расходы)."""
        return round(self.get_total_income() - self.get_total_expenses(), 2)

    def get_category_breakdown(self, trans_type: TransactionType = TransactionType.EXPENSE) -> Dict[str, float]:
        """Сводка сумм по категориям (для расходов или доходов)."""
        breakdown: Dict[str, float] = {}
        for t in self._transactions:
            if t.type == trans_type:
                breakdown[t.category] = round(breakdown.get(t.category, 0.0) + t.amount, 2)
        return breakdown

    def get_summary(self) -> dict:
        """Полная сводка по счету."""
        return {
            "total_income": self.get_total_income(),
            "total_expenses": self.get_total_expenses(),
            "balance": self.get_balance(),
            "transactions_count": len(self._transactions),
            "expenses_by_category": self.get_category_breakdown(TransactionType.EXPENSE),
            "income_by_category": self.get_category_breakdown(TransactionType.INCOME)
        }

    def clear(self) -> None:
        """Очистить все записи."""
        self._transactions.clear()
        self._next_id = 1
        if self.storage_path and os.path.exists(self.storage_path):
            self.save_to_file(self.storage_path)

    def save_to_file(self, filepath: str) -> None:
        """Сохранить состояние в JSON-файл."""
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        payload = {
            "next_id": self._next_id,
            "transactions": [t.to_dict() for t in self._transactions]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str) -> None:
        """Загрузить операции из JSON-файла."""
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return

        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self._next_id = payload.get("next_id", 1)
        raw_items = payload.get("transactions", [])
        self._transactions = [Transaction.from_dict(item) for item in raw_items]

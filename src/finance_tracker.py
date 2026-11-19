import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import Dict, Generator, List, Optional


class TransactionType(str, Enum):
    """Тип финансовой операции."""
    INCOME = "income"
    EXPENSE = "expense"


class Transaction:
    """Модель финансовой операции."""

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
        return {
            "id": self.id,
            "amount": self.amount,
            "type": self.type.value,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at
        }


class PersonalFinanceTracker:
    """
    Класс учета личных средств на базе базы данных SQLite.
    Обеспечивает надежное хранение без потери данных между процессами и рабочими потоками.
    """

    def __init__(self, db_path: Optional[str] = None, storage_path: Optional[str] = None):
        self.db_path = db_path or storage_path or ":memory:"
        self._is_memory = (self.db_path == ":memory:")
        self._mem_conn = None

        if self._is_memory:
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
        else:
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        if self._is_memory:
            with self._mem_conn:
                yield self._mem_conn
        else:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            conn.row_factory = sqlite3.Row
            try:
                with conn:
                    yield conn
            finally:
                conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)

    def add_transaction(
        self,
        amount: float,
        trans_type: TransactionType,
        category: str,
        description: str = "",
        created_at: Optional[str] = None
    ) -> Transaction:
        """Добавить операцию в базу данных."""
        if amount <= 0:
            raise ValueError("Сумма операции должна быть строго положительным числом.")
        if not category or not category.strip():
            raise ValueError("Категория операции не может быть пустой.")

        type_val = trans_type.value if isinstance(trans_type, TransactionType) else str(trans_type)
        date_str = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cat_clean = category.strip()
        desc_clean = description.strip() if description else ""
        amount_round = round(float(amount), 2)

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions (amount, type, category, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (amount_round, type_val, cat_clean, desc_clean, date_str)
            )
            trans_id = cursor.lastrowid

        return Transaction(
            trans_id=trans_id,
            amount=amount_round,
            trans_type=TransactionType(type_val),
            category=cat_clean,
            description=desc_clean,
            created_at=date_str
        )

    def add_income(self, amount: float, category: str, description: str = "") -> Transaction:
        return self.add_transaction(amount, TransactionType.INCOME, category, description)

    def add_expense(self, amount: float, category: str, description: str = "") -> Transaction:
        return self.add_transaction(amount, TransactionType.EXPENSE, category, description)

    def delete_transaction(self, trans_id: int) -> bool:
        """Удалить операцию по идентификатору."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            return cursor.rowcount > 0

    def get_transactions(
        self,
        trans_type: Optional[TransactionType] = None,
        category: Optional[str] = None
    ) -> List[Transaction]:
        """Получить список всех операций с сортировкой от новых к старым."""
        query = "SELECT id, amount, type, category, description, created_at FROM transactions WHERE 1=1"
        params = []

        if trans_type:
            val = trans_type.value if isinstance(trans_type, TransactionType) else str(trans_type)
            query += " AND type = ?"
            params.append(val)

        if category:
            query += " AND lower(category) = lower(?)"
            params.append(category)

        query += " ORDER BY id DESC"

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Transaction(
                trans_id=r["id"],
                amount=r["amount"],
                trans_type=TransactionType(r["type"]),
                category=r["category"],
                description=r["description"],
                created_at=r["created_at"]
            )
            for r in rows
        ]

    def get_total_income(self) -> float:
        """Сумма всех доходов."""
        with self._connection() as conn:
            res = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = ?",
                (TransactionType.INCOME.value,)
            ).fetchone()[0]
        return round(float(res), 2)

    def get_total_expenses(self) -> float:
        """Сумма всех расходов."""
        with self._connection() as conn:
            res = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = ?",
                (TransactionType.EXPENSE.value,)
            ).fetchone()[0]
        return round(float(res), 2)

    def get_balance(self) -> float:
        """Текущий баланс (доходы минус расходы)."""
        return round(self.get_total_income() - self.get_total_expenses(), 2)

    def get_category_breakdown(self, trans_type: TransactionType = TransactionType.EXPENSE) -> Dict[str, float]:
        """Сводка сумм по категориям."""
        val = trans_type.value if isinstance(trans_type, TransactionType) else str(trans_type)
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT category, ROUND(SUM(amount), 2) as total
                FROM transactions
                WHERE type = ?
                GROUP BY category
                ORDER BY total DESC
                """,
                (val,)
            ).fetchall()
        return {r["category"]: float(r["total"]) for r in rows}

    def get_summary(self) -> dict:
        """Общая сводка состояния счета."""
        return {
            "total_income": self.get_total_income(),
            "total_expenses": self.get_total_expenses(),
            "balance": self.get_balance(),
            "transactions_count": len(self.get_transactions()),
            "expenses_by_category": self.get_category_breakdown(TransactionType.EXPENSE),
            "income_by_category": self.get_category_breakdown(TransactionType.INCOME)
        }

    def clear(self) -> None:
        """Очистить все записи."""
        with self._connection() as conn:
            conn.execute("DELETE FROM transactions")

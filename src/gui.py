"""
Графический интерфейс на Tkinter для калькулятора личных средств.
(Локальный десктопный режим согласно заданию).
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from src.finance_tracker import PersonalFinanceTracker, TransactionType

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STORAGE_PATH = os.path.join(DATA_DIR, "finance_data.json")


class FinanceTrackerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Калькулятор личных средств (Личный бюджет)")
        self.root.geometry("750x600")
        self.root.minsize(650, 500)

        self.tracker = PersonalFinanceTracker(storage_path=STORAGE_PATH)

        self._build_ui()
        self._refresh_data()

    def _build_ui(self):
        # Верхняя панель со сводкой (Баланс, Доход, Расход)
        summary_frame = ttk.LabelFrame(self.root, text="Финансовая сводка", padding=10)
        summary_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_balance = ttk.Label(summary_frame, text="Баланс: 0.00 ₽", font=("Arial", 12, "bold"))
        self.lbl_balance.pack(side="left", expand=True)

        self.lbl_income = ttk.Label(summary_frame, text="Доходы: +0.00 ₽", foreground="green", font=("Arial", 10))
        self.lbl_income.pack(side="left", expand=True)

        self.lbl_expense = ttk.Label(summary_frame, text="Расходы: -0.00 ₽", foreground="red", font=("Arial", 10))
        self.lbl_expense.pack(side="left", expand=True)

        # Панель добавления операции
        add_frame = ttk.LabelFrame(self.root, text="Добавить операцию", padding=10)
        add_frame.pack(fill="x", padx=10, pady=5)

        # Тип (Доход / Расход)
        ttk.Label(add_frame, text="Тип:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.var_type = tk.StringVar(value="expense")
        type_box = ttk.Combobox(add_frame, textvariable=self.var_type, state="readonly", width=12)
        type_box["values"] = ("expense", "income")
        type_box.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Сумма
        ttk.Label(add_frame, text="Сумма (₽):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.entry_amount = ttk.Entry(add_frame, width=15)
        self.entry_amount.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        # Категория
        ttk.Label(add_frame, text="Категория:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_category = ttk.Combobox(add_frame, width=15)
        self.entry_category["values"] = (
            "Продукты", "Транспорт", "Жилье", "Зарплата", "Фриланс", "Кафе", "Развлечения", "Здоровье"
        )
        self.entry_category.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Описание
        ttk.Label(add_frame, text="Описание:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.entry_desc = ttk.Entry(add_frame, width=25)
        self.entry_desc.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Кнопка добавления
        btn_add = ttk.Button(add_frame, text="Добавить", command=self._add_action)
        btn_add.grid(row=1, column=4, padx=10, pady=5)

        # Таблица операций
        table_frame = ttk.LabelFrame(self.root, text="История операций", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "date", "type", "category", "amount", "desc")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("id", text="#")
        self.tree.heading("date", text="Дата")
        self.tree.heading("type", text="Тип")
        self.tree.heading("category", text="Категория")
        self.tree.heading("amount", text="Сумма (₽)")
        self.tree.heading("desc", text="Описание")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("date", width=140, anchor="center")
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("category", width=120)
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("desc", width=200)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Нижняя панель действий (Удалить)
        bottom_frame = ttk.Frame(self.root, padding=5)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        btn_delete = ttk.Button(bottom_frame, text="Удалить выбранную запись", command=self._delete_selected)
        btn_delete.pack(side="right", padx=5)

    def _add_action(self):
        try:
            raw_amount = self.entry_amount.get().strip().replace(",", ".")
            if not raw_amount:
                messagebox.showerror("Ошибка", "Введите сумму операции")
                return

            amount = float(raw_amount)
            category = self.entry_category.get().strip()
            if not category:
                messagebox.showerror("Ошибка", "Укажите категорию")
                return

            t_type = TransactionType(self.var_type.get())
            desc = self.entry_desc.get().strip()

            self.tracker.add_transaction(amount, t_type, category, desc)

            # Очистка полей
            self.entry_amount.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)

            self._refresh_data()
        except ValueError as ex:
            messagebox.showerror("Ошибка", str(ex))

    def _delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return

        values = self.tree.item(selected_item[0], "values")
        trans_id = int(values[0])
        self.tracker.delete_transaction(trans_id)
        self._refresh_data()

    def _refresh_data(self):
        # Очистить таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Заполнить операциями
        transactions = self.tracker.get_transactions()
        for t in transactions:
            t_type_ru = "Доход" if t.type == TransactionType.INCOME else "Расход"
            sign = "+" if t.type == TransactionType.INCOME else "-"
            self.tree.insert("", "end", values=(
                t.id,
                t.created_at,
                t_type_ru,
                t.category,
                f"{sign}{t.amount:.2f}",
                t.description
            ))

        # Обновить сводку
        summary = self.tracker.get_summary()
        self.lbl_balance.config(text=f"Баланс: {summary['balance']:.2f} ₽")
        self.lbl_income.config(text=f"Доходы: +{summary['total_income']:.2f} ₽")
        self.lbl_expense.config(text=f"Расходы: -{summary['total_expenses']:.2f} ₽")


def main():
    root = tk.Tk()
    FinanceTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

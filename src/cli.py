"""
Консольный интерфейс (CLI) для калькулятора личных средств.
"""
import argparse
from src.finance_tracker import PersonalFinanceTracker, TransactionType


def main():
    parser = argparse.ArgumentParser(description="CLI Калькулятор личных средств")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # add-income
    inc = subparsers.add_parser("income", help="Добавить доход")
    inc.add_argument("amount", type=float, help="Сумма")
    inc.add_argument("category", type=str, help="Категория")
    inc.add_argument("-d", "--desc", default="", help="Описание")

    # add-expense
    exp = subparsers.add_parser("expense", help="Добавить расход")
    exp.add_argument("amount", type=float, help="Сумма")
    exp.add_argument("category", type=str, help="Категория")
    exp.add_argument("-d", "--desc", default="", help="Описание")

    # summary
    subparsers.add_parser("summary", help="Показать баланс и сводку")

    # list
    subparsers.add_parser("list", help="Показать список операций")

    args = parser.parse_args()
    tracker = PersonalFinanceTracker(storage_path="data/finance_data.json")

    if args.command == "income":
        t = tracker.add_income(args.amount, args.category, args.desc)
        print(f"✅ Доход успешно добавлен: +{t.amount:.2f} ₽ ({t.category})")
    elif args.command == "expense":
        t = tracker.add_expense(args.amount, args.category, args.desc)
        print(f"✅ Расход успешно добавлен: -{t.amount:.2f} ₽ ({t.category})")
    elif args.command == "summary":
        s = tracker.get_summary()
        print("\n--- Финансовая сводка ---")
        print(f"Доходы:  +{s['total_income']:.2f} ₽")
        print(f"Расходы: -{s['total_expenses']:.2f} ₽")
        print(f"Баланс:   {s['balance']:.2f} ₽")
        print("------------------------\n")
    elif args.command == "list":
        txs = tracker.get_transactions()
        if not txs:
            print("История операций пуста.")
            return
        print(f"\nВсего операций: {len(txs)}")
        for t in txs:
            sign = "+" if t.type == TransactionType.INCOME else "-"
            print(f"[{t.id}] {t.created_at} | {sign}{t.amount:.2f} ₽ | {t.category} | {t.description}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

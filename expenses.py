"""Project 3: Expense Tracker (saved to CSV)

Run: python expenses.py
"""
import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

FILE = Path("expenses.csv")
FIELDS = ["date", "amount", "category", "note"]


# ---------- storage ----------
def load_expenses():
    if not FILE.exists():
        return []
    with FILE.open(newline="") as f:
        rows = list(csv.DictReader(f))
    # CSV stores everything as text, so convert amount back to a number
    for row in rows:
        row["amount"] = float(row["amount"])
    return rows


def append_expense(expense):
    is_new = not FILE.exists()
    with FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(expense)


# ---------- input helpers ----------
def ask_amount():
    while True:
        text = input("Amount: ").strip()
        try:
            amount = float(text)
        except ValueError:
            print("Please enter a number, e.g. 250 or 99.50")
            continue
        if amount <= 0:
            print("Amount must be greater than 0.")
            continue
        return round(amount, 2)


def ask_date():
    while True:
        text = input("Date (YYYY-MM-DD, leave empty for today): ").strip()
        if not text:
            return date.today().isoformat()
        try:
            return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
        except ValueError:
            print("Invalid date. Use the format 2026-10-23.")


def ask_category():
    while True:
        category = input("Category (food, travel, bills...): ").strip().lower()
        if category:
            return category
        print("Category cannot be empty.")


# ---------- actions ----------
def add():
    expense = {
        "date": ask_date(),
        "amount": ask_amount(),
        "category": ask_category(),
        "note": input("Note (optional): ").strip(),
    }
    append_expense(expense)
    print("Expense saved.")


def view():
    expenses = load_expenses()
    if not expenses:
        print("No expenses yet.")
        return
    print(f"{'Date':<12}{'Amount':>10}  {'Category':<12}Note")
    for e in sorted(expenses, key=lambda e: e["date"]):
        print(f"{e['date']:<12}{e['amount']:>10.2f}  {e['category']:<12}{e['note']}")


def summary():
    expenses = load_expenses()
    if not expenses:
        print("No expenses yet.")
        return

    by_category = defaultdict(float)  # missing keys start at 0.0
    by_month = defaultdict(float)
    for e in expenses:
        by_category[e["category"]] += e["amount"]
        by_month[e["date"][:7]] += e["amount"]  # "2026-10-23" -> "2026-10"

    total = sum(e["amount"] for e in expenses)
    print(f"\nTotal spent: {total:.2f}")

    print("\nBy category:")
    for category, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:<12}{amount:>10.2f}")

    print("\nBy month:")
    for month, amount in sorted(by_month.items()):
        print(f"  {month:<12}{amount:>10.2f}")


def main():
    actions = {"add": add, "view": view, "summary": summary}
    try:
        while True:
            cmd = input("\nCommand (add, view, summary, exit): ").strip().lower()
            if cmd == "exit":
                break
            action = actions.get(cmd)
            if action:
                action()
            else:
                print("Invalid command.")
    except (EOFError, KeyboardInterrupt):
        print()
    print("Bye!")


if __name__ == "__main__":
    main()

"""Project 2: To-Do List (interactive menu, saved to JSON)

Run: python todo.py
"""
import json
from datetime import datetime
from pathlib import Path

FILE = Path("tasks.json")


def now():
    """Current time as a string, because datetime objects can't go into JSON."""
    return datetime.now().isoformat(timespec="seconds")


def ask_non_empty(prompt):
    """Keep asking until the user types something other than spaces."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


class TodoApp:
    def __init__(self):
        # Every task is a plain dict, both in memory and in the file:
        # {"id": 1, "title": "...", "person": "...", "done": False,
        #  "created_at": "...", "updated_at": "..."}
        self.tasks = self.load()

    # ---------- storage ----------
    def load(self):
        if not FILE.exists():
            return []
        text = FILE.read_text().strip()
        if not text:
            return []
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Warning: {FILE} is corrupted, starting with an empty list.")
            return []

    def save(self):
        FILE.write_text(json.dumps(self.tasks, indent=2))

    # ---------- helpers ----------
    def next_id(self):
        return self.tasks[-1]["id"] + 1 if self.tasks else 1

    def find(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def ask_task(self):
        """Ask for an id and return the matching task, or None."""
        text = input("Task id: ").strip()
        if not text.isdigit():
            print("Please enter a number.")
            return None
        task = self.find(int(text))
        if task is None:
            print(f"No task with id {text}.")
        return task

    # ---------- actions ----------
    def add(self):
        title = ask_non_empty("Task: ")
        person = ask_non_empty("Assign to: ")
        task = {
            "id": self.next_id(),
            "title": title,
            "person": person,
            "done": False,
            "created_at": now(),
            "updated_at": now(),
        }
        self.tasks.append(task)
        self.save()
        print(f"Added task #{task['id']}.")

    def list(self):
        if not self.tasks:
            print("No tasks yet.")
            return
        for task in self.tasks:
            mark = "x" if task["done"] else " "
            print(f"[{mark}] #{task['id']} {task['title']}  (→ {task['person']})")

    def mark_done(self):
        task = self.ask_task()
        if task:
            task["done"] = True
            task["updated_at"] = now()
            self.save()
            print(f"Task #{task['id']} marked done.")

    def delete(self):
        task = self.ask_task()
        if task:
            self.tasks.remove(task)
            self.save()
            print(f"Task #{task['id']} deleted.")


def main():
    app = TodoApp()
    actions = {
        "add": app.add,
        "list": app.list,
        "done": app.mark_done,
        "delete": app.delete,
    }

    try:
        while True:
            cmd = input("\nCommand (add, list, done, delete, exit): ").strip().lower()
            if cmd == "exit":
                break
            action = actions.get(cmd)
            if action:
                action()
            else:
                print("Invalid command.")
    except (EOFError, KeyboardInterrupt):
        print()  # Ctrl+D / Ctrl+C: exit quietly instead of a traceback

    print("Bye!")


if __name__ == "__main__":
    main()

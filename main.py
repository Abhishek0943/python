"""Project 6: To-Do REST API with FastAPI

Setup (with uv):
    uv init todo-api && cd todo-api
    uv add fastapi uvicorn
    (put this file in the folder as main.py)

    Only fastapi and uvicorn need installing. pydantic is installed
    automatically as a dependency of fastapi. json, datetime, pathlib and
    typing are part of Python's standard library, so they're already there.

Run:
    uv run uvicorn main:app --reload

Then open http://localhost:8000/docs to try every endpoint in the browser.

Endpoints:
    GET    /tasks              list tasks  (?done=true  ?person=Rahul  ?skip=0&limit=10)
    GET    /tasks/{task_id}    get one task
    POST   /tasks              create a task
    PUT    /tasks/{task_id}    update title / description / person / done
    DELETE /tasks/{task_id}    delete a task
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, StringConstraints

# A string that is stripped of surrounding spaces and must not be empty.
# "" or "   " -> FastAPI automatically returns 422.
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# ---------- models (request / response shapes) ----------
class TaskCreate(BaseModel):
    """What the client sends to create a task."""
    title: NonEmptyStr
    person: NonEmptyStr
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    """What the client sends to update a task. Every field is optional,
    so the client only sends what it wants to change."""
    title: Optional[NonEmptyStr] = None
    person: Optional[NonEmptyStr] = None
    description: Optional[str] = None
    done: Optional[bool] = None


class Task(BaseModel):
    """What the API returns. The server sets id, done and the timestamps."""
    id: int
    title: str
    person: str
    description: Optional[str] = None
    done: bool = False
    created_at: str
    updated_at: str


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------- storage ----------
class TaskStore:
    """Keeps tasks in memory and mirrors them to a JSON file shaped like:
    {"last_id": 3, "tasks": [ {...}, {...} ]}

    last_id is saved so ids are never reused after a delete. Otherwise a
    client still holding /tasks/2 could get a different, newer task."""

    def __init__(self, path: str = "data.json"):
        self.path = Path(path)
        self.last_id = 0
        self.tasks: list[dict] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        text = self.path.read_text().strip()
        if not text:
            return
        try:
            saved = json.loads(text)
        except json.JSONDecodeError:
            print(f"Warning: {self.path} is corrupted, starting with an empty list.")
            return
        self.tasks = saved.get("tasks", [])
        self.last_id = saved.get("last_id", max((t["id"] for t in self.tasks), default=0))

    def save(self) -> None:
        data = {"last_id": self.last_id, "tasks": self.tasks}
        self.path.write_text(json.dumps(data, indent=2))

    def next_id(self) -> int:
        self.last_id += 1
        return self.last_id

    def find(self, task_id: int) -> Optional[dict]:
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def list(self, done: Optional[bool], person: Optional[str], skip: int, limit: int) -> list[dict]:
        result = self.tasks
        if done is not None:
            result = [t for t in result if t["done"] == done]
        if person:
            result = [t for t in result if t["person"].lower() == person.strip().lower()]
        return result[skip:skip + limit]

    def add(self, new: TaskCreate) -> dict:
        timestamp = now()
        task = Task(id=self.next_id(), created_at=timestamp, updated_at=timestamp,
                    **new.model_dump())
        self.tasks.append(task.model_dump())
        self.save()
        return self.tasks[-1]

    def update(self, task_id: int, changes: TaskUpdate) -> Optional[dict]:
        task = self.find(task_id)
        if task is None:
            return None
        # Only the fields the client actually sent, ignoring nulls
        updates = changes.model_dump(exclude_unset=True, exclude_none=True)
        if updates:
            task.update(updates)
            task["updated_at"] = now()
            self.save()
        return task

    def delete(self, task_id: int) -> bool:
        task = self.find(task_id)
        if task is None:
            return False
        self.tasks.remove(task)
        self.save()
        return True


# ---------- API ----------
app = FastAPI(title="To-Do API")
store = TaskStore()


def get_or_404(task_id: int) -> dict:
    task = store.find(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    done: Optional[bool] = None,
    person: Optional[str] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return store.list(done, person, skip, limit)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    return get_or_404(task_id)


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(new: TaskCreate):
    return store.add(new)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, changes: TaskUpdate):
    task = store.update(task_id, changes)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    if not store.delete(task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
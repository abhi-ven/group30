"""Synthetic demo student.

Times are built relative to today so the demo always shows a live day.
Shape follows the shared data model (Task, FixedEvent, Plan, PlanBlock).
"""
from datetime import datetime, timedelta


def _at(day: datetime, hhmm: str) -> str:
    h, m = map(int, hhmm.split(":"))
    return day.replace(hour=h, minute=m, second=0, microsecond=0).isoformat(timespec="minutes")


def load_sample_state() -> dict:
    today = datetime.now()
    day = lambda n: today + timedelta(days=n)

    fixed_events = [
        {"id": "f1", "title": "COMP20010 Algorithms lecture", "start": _at(today, "11:00"),
         "end": _at(today, "12:00"), "source": "ics", "kind": "lecture", "protected": True},
        {"id": "f2", "title": "Lunch", "start": _at(today, "12:00"),
         "end": _at(today, "13:00"), "source": "manual", "kind": "meal", "protected": True},
        {"id": "f3", "title": "Group project meeting", "start": _at(today, "14:00"),
         "end": _at(today, "15:00"), "source": "manual", "kind": "meeting", "protected": True},
    ]

    def task(id, title, ttype, due, est, remaining, weighting, status, snippet=None):
        return {
            "id": id, "title": title, "taskType": ttype, "due": due,
            "estimatedMinutes": est, "actualMinutes": None, "remainingMinutes": remaining,
            "weighting": weighting, "priority": 0, "parentId": None, "source": "pdf",
            "sourceSnippet": snippet, "confidence": "high", "status": status,
        }

    tasks = [
        task("t1", "Algorithms lab report", "lab_report", _at(day(1), "17:00"), 360, 180, 15,
             "in_progress", "Submit via Brightspace by 5pm Friday."),
        task("t2", "Statistics problem set 4", "problem_set", _at(day(3), "23:59"), 150, 150, 10, "todo"),
        task("t3", "Databases reading, chapter 6", "reading", _at(day(5), "12:00"), 90, 90, None, "todo"),
        task("t4", "Software project milestone 2", "project", _at(day(6), "17:00"), 480, 420, 20, "todo"),
        task("t5", "Quiz 2 revision", "revision", _at(day(-1), "10:00"), 60, 0, 5, "done"),
    ]

    blocks = [
        {"id": "b1", "start": _at(today, "09:30"), "end": _at(today, "11:00"), "type": "task", "refId": "t1"},
        {"id": "b2", "start": _at(today, "11:00"), "end": _at(today, "12:00"), "type": "fixed", "refId": "f1"},
        {"id": "b3", "start": _at(today, "12:00"), "end": _at(today, "13:00"), "type": "fixed", "refId": "f2"},
        {"id": "b4", "start": _at(today, "13:00"), "end": _at(today, "14:00"), "type": "task", "refId": "t1"},
        {"id": "b5", "start": _at(today, "14:00"), "end": _at(today, "15:00"), "type": "fixed", "refId": "f3"},
        {"id": "b6", "start": _at(today, "15:00"), "end": _at(today, "15:15"), "type": "break", "refId": "break"},
        {"id": "b7", "start": _at(today, "15:15"), "end": _at(today, "15:45"), "type": "task", "refId": "t2"},
    ]

    return {
        "student": {"name": "Aoife", "course": "BSc Computer Science, Year 2"},
        "fixed_events": fixed_events,
        "tasks": tasks,
        "plan": {"id": "p1", "date": today.date().isoformat(), "blocks": blocks,
                 "warnings": ["The lab report is due tomorrow at 17:00 and still needs 3 hours of work."]},
    }
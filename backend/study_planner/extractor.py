from datetime import datetime

from .config import get_model
from .helpers import DUBLIN
from .pdf_reader import parse_json
from .prompts import EXTRACT_PROMPT

TYPES = ['lab_report', 'essay', 'problem_set', 'reading', 'revision', 'project', 'other']


def to_iso(date, time):
    """Local Dublin date/time -> ISO string with offset, or None."""
    if not date or str(date).lower() == 'null':
        return None
    if not time or str(time).lower() == 'null':
        time = "23:59"  # date given but no time: end of day
    local = datetime.fromisoformat(f"{date}T{time}").replace(tzinfo=DUBLIN)
    return local.isoformat(timespec="minutes")


def to_weight(value):
    """Models sometimes return '40' or '40%'. Turn it into a number or None."""
    if value is None:
        return None
    try:
        number = float(str(value).replace('%', '').strip())
    except ValueError:
        return None
    return number if 0 <= number <= 100 else None


def extract_tasks(text):
    """Use with helpers.extract_review(text, extractor=extract_tasks)."""
    reply = get_model().invoke([("system", EXTRACT_PROMPT),
                                ("human", "Analyse this assignment brief:\n\n" + text)])
    data = parse_json(reply.content)
    tasks = []
    for item in data["tasks"]:
        task_type = item.get("taskType")
        tasks.append({
            "title": item["title"],
            "taskType": task_type if task_type in TYPES else "other",
            "due": to_iso(item.get("dueDate"), item.get("dueTime")),
            "estimatedMinutes": max(1, round(float(item["estimatedHours"]) * 60)),
            "weighting": to_weight(item.get("weighting")),
            "source": "pdf",
        })
    return {"tasks": tasks}

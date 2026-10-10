TASK_TYPES = "lab_report|essay|problem_set|reading|revision|project|other"

EXTRACT_PROMPT = f"""You read an academic assignment brief and break it into
actionable study tasks. Report only facts stated in the brief. Never invent a
deadline or weighting: use null if it is not explicitly given.
Split the work into subtasks. Give each subtask the assignment's due date and
weighting. Estimate effort in hours for each subtask (this is your estimate).

Return ONLY valid JSON, no commentary, in this shape:
{{"tasks": [{{"title": "", "taskType": "{TASK_TYPES}",
  "dueDate": "YYYY-MM-DD or null", "dueTime": "HH:MM or null",
  "estimatedHours": 1.5, "weighting": "number 0-100 or null"}}]}}"""

DISRUPTION_PROMPT = """You convert a student's message about a disruption into
JSON. Use ONLY the IDs given in the context. Return ONLY one JSON object of
exactly one of these forms:
{"type":"lost_time","minutes":120}
{"type":"task_takes_longer","taskId":"...","multiplier":2}
{"type":"missed_session","blockId":"..."}
{"type":"cancelled_event","eventId":"..."}
{"type":"late_running_event","eventId":"...","minutes":30}
{"type":"urgent_task","newTask":{"title":"","estimatedMinutes":60,
  "due":"ISO time with offset, e.g. 2026-10-11T12:00:00+01:00","weighting":null}}
If the message fits none of them, return {"type":"unknown"}."""

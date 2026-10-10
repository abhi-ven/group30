EXTRACT_PROMPT = '''Read an academic assignment brief and break it into actionable
subtasks. Never invent a deadline or the assignment's overall module weighting;
use null if not stated. Estimate effort in hours per subtask, as a suggestion.
Do not also include a summary parent task. Use one taskType from:
lab_report, essay, problem_set, reading, revision, project, other.
Return JSON only:
{"tasks":[{"title":"", "taskType":"other", "dueDate":null,
"dueTime":null, "estimatedHours":1.5, "weighting":null}]}'''

DISRUPTION_PROMPT = '''Convert the student's disruption into one JSON object.
Use only IDs supplied in context. Do not generate schedule blocks or invent tasks.
Class timestamps and study blocks are in Dublin time. Select the class that the
student describes; ask through an unknown result if the reference is ambiguous.
Supported forms:
{"type":"lost_time","minutes":120}
{"type":"task_takes_longer","taskId":"...","multiplier":2}
{"type":"missed_session","blockId":"..."}
{"type":"cancelled_event","eventId":"..."}
{"type":"late_running_event","eventId":"...","minutes":30}
{"type":"urgent_task","newTask":{"title":"","estimatedMinutes":60,"due":null,"weighting":null}}
For a new task, set missing due/weighting to null; never fabricate them.
For unsupported or ambiguous messages return {"type":"unknown"}.
Return JSON only.'''

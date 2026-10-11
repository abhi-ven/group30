from datetime import datetime
from math import isfinite
from .config import get_model
from .helpers import DUBLIN
from .pdf_reader import parse_json
from .prompts import EXTRACT_PROMPT

TYPES = ['lab_report', 'essay', 'problem_set', 'reading', 'revision', 'project', 'other']


def to_iso(day, clock):
    if not day or str(day).lower() == 'null':
        return None
    # Explicit app convention: a date without a time means 23:59 Dublin.
    if not clock or str(clock).lower() == 'null':
        clock = '23:59'
    return datetime.fromisoformat(f'{day}T{clock}').replace(tzinfo=DUBLIN).isoformat(timespec='minutes')


def to_weight(value):
    if value is None:
        return None
    try:
        number = float(str(value).replace('%', '').strip())
    except ValueError:
        return None
    return number if isfinite(number) and 0 <= number <= 100 else None


def extract_tasks(text):
    reply = get_model().invoke([('system', EXTRACT_PROMPT), ('human', text)])
    data = parse_json(reply.content)
    tasks = []
    for item in data['tasks']:
        hours = float(item['estimatedHours'])
        if not isfinite(hours) or hours <= 0:
            raise ValueError('Invalid effort estimate')
        kind = item.get('taskType')
        tasks.append({'title': item['title'], 'taskType': kind if kind in TYPES else 'other',
                      'due': to_iso(item.get('dueDate'), item.get('dueTime')),
                      'estimatedMinutes': max(1, round(hours * 60)),
                      'weighting': to_weight(item.get('weighting')), 'source': 'pdf'})
    return {'tasks': tasks}

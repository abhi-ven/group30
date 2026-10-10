"""Small shared functions: validation, conflict checks, comparisons and mock AI.

All inputs and outputs are ordinary dictionaries and lists.
"""
from copy import deepcopy
from datetime import datetime, timezone
from math import isfinite
from zoneinfo import ZoneInfo
from uuid import uuid4
import json
import re

DUBLIN = ZoneInfo('Europe/Dublin')


def read_time(value):
    """Turn an ISO string into a datetime so Python can compare times."""
    if not isinstance(value, str):
        raise ValueError('A time must be an ISO string')
    time = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if time.tzinfo is None:
        raise ValueError('Times need a timezone, such as +01:00')
    if time.second != 0 or time.microsecond != 0:
        raise ValueError('Use whole minutes, without seconds')
    # UTC makes subtraction correct even when the clocks change.
    return time.astimezone(timezone.utc)


def write_time(time):
    return time.astimezone(DUBLIN).isoformat()


def duration_minutes(start, end):
    difference = read_time(end) - read_time(start)
    return int(difference.total_seconds() / 60)


def check_number(value, name, minimum=0, maximum=525600):
    if type(value) is not int:
        raise ValueError(name + ' must be a whole number')
    if value < minimum or value > maximum:
        raise ValueError(name + ' is outside the allowed range')


def check_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + ' must be a non-empty string')


def check_choice(value, options, name):
    if value not in options:
        raise ValueError('Invalid ' + name)


def validate_task(task):
    """Check an extracted task and fill optional fields with safe defaults."""
    task = deepcopy(task)
    # IDs are created here; the PDF extractor does not need to supply them.
    task.setdefault('id', str(uuid4()))
    # Ignore these fields if an older extractor still sends them.
    task.pop('sourceSnippet', None)
    task.pop('confidence', None)
    check_text(task['id'], 'Task ID')
    check_text(task['title'], 'Task title')
    check_number(task['estimatedMinutes'], 'estimatedMinutes', 1)
    task.setdefault('remainingMinutes', task['estimatedMinutes'])
    task.setdefault('due', None)
    task.setdefault('actualMinutes', None)
    task.setdefault('weighting', None)
    task.setdefault('taskType', 'other')
    task.setdefault('parentId', None)
    task.setdefault('source', 'manual')
    task.setdefault('status', 'todo')
    task['priority'] = 0  # The scheduler will compute this, not the AI.

    check_number(task['remainingMinutes'], 'remainingMinutes')
    if task['actualMinutes'] is not None:
        check_number(task['actualMinutes'], 'actualMinutes')
    if task['due'] is not None:
        read_time(task['due'])
    weight = task['weighting']
    if weight is not None:
        if type(weight) not in (int, float) or not isfinite(weight) or not 0 <= weight <= 100:
            raise ValueError('weighting must be null or between 0 and 100')
    check_choice(task['source'], ['ics', 'pdf', 'paste', 'manual'], 'source')
    check_choice(task['taskType'], ['lab_report', 'essay', 'problem_set', 'reading', 'revision', 'project', 'other'], 'taskType')
    check_choice(task['status'], ['todo', 'in_progress', 'done', 'at_risk'], 'status')
    if task['status'] == 'done' and task['remainingMinutes'] != 0:
        raise ValueError('Done tasks must have zero remaining minutes')
    if task['parentId'] is not None and not isinstance(task['parentId'], str):
        raise ValueError('parentId must be null or a string')
    return task


def same_assignment(first, second):
    # Different parents and sources can represent different assignments.
    return (first['title'].strip().lower() == second['title'].strip().lower()
            and first['due'] == second['due']
            and first['parentId'] == second['parentId']
            and first['source'] == second['source'])


def prepare_tasks(tasks):
    """Merge matching duplicates so an imported task is not scheduled twice."""
    result = []
    seen_ids = {}
    for original in tasks:
        task = validate_task(original)
        if task['id'] in seen_ids and seen_ids[task['id']] != task:
            raise ValueError('Conflicting task ID: ' + task['id'])
        seen_ids[task['id']] = deepcopy(task)
        match = None
        for existing in result:
            if same_assignment(existing, task):
                match = existing
                break
        if match is None:
            result.append(task)
        else:
            if (match['status'] == 'done') != (task['status'] == 'done'):
                raise ValueError('Duplicates disagree about completion')
            match['remainingMinutes'] = max(match['remainingMinutes'], task['remainingMinutes'])
            match['estimatedMinutes'] = max(match['estimatedMinutes'], task['estimatedMinutes'])
            if task['weighting'] is not None:
                match['weighting'] = max(match['weighting'] or 0, task['weighting'])
    return result


def time_order(block):
    return read_time(block['start'])


def intervals_overlap(first, second):
    return (read_time(first['start']) < read_time(second['end'])
            and read_time(second['start']) < read_time(first['end']))


def merge_windows(windows):
    """Combine overlapping or adjacent availability before scheduling."""
    result = []
    for window in sorted(windows, key=time_order):
        window = deepcopy(window)
        if result and read_time(window['start']) <= read_time(result[-1]['end']):
            if read_time(window['end']) > read_time(result[-1]['end']):
                result[-1]['end'] = window['end']
        else:
            result.append(window)
    return result


def remove_interval(windows, busy):
    """Subtract one occupied interval. A window can split into two gaps."""
    result = []
    for window in windows:
        if not intervals_overlap(window, busy):
            result.append(deepcopy(window))
            continue
        if read_time(window['start']) < read_time(busy['start']):
            result.append({'start': window['start'], 'end': busy['start']})
        if read_time(busy['end']) < read_time(window['end']):
            result.append({'start': busy['end'], 'end': window['end']})
    return result


def make_block(identifier, start, end, block_type, reference):
    return {'id': identifier, 'start': write_time(start), 'end': write_time(end),
            'type': block_type, 'refId': reference, 'changeStatus': 'unchanged'}


def check_plan(plan, state):
    """Independent checks: reject invalid plans instead of displaying them."""
    errors = []
    blocks = sorted(plan['blocks'], key=time_order)
    ids = set()
    for index in range(len(blocks)):
        block = blocks[index]
        if block['id'] in ids:
            errors.append('Duplicate block ID: ' + block['id'])
        ids.add(block['id'])
        if read_time(block['end']) <= read_time(block['start']):
            errors.append('Invalid block duration: ' + block['id'])
        for earlier in blocks[:index]:
            if intervals_overlap(earlier, block):
                errors.append('Overlapping blocks: ' + earlier['id'] + ' and ' + block['id'])

    for event in state['fixedEvents']:
        matches = []
        for block in blocks:
            if block['type'] == 'fixed' and block['refId'] == event['id']:
                matches.append(block)
        if len(matches) != 1:
            errors.append('Fixed event missing or duplicated: ' + event['id'])
        elif (read_time(matches[0]['start']) != read_time(event['start'])
              or read_time(matches[0]['end']) != read_time(event['end'])):
            errors.append('Fixed event was changed: ' + event['id'])

    task_map = {}
    scheduled = {}
    event_ids = set()
    for event in state['fixedEvents']:
        event_ids.add(event['id'])
    for task in state['tasks']:
        task_map[task['id']] = task
        scheduled[task['id']] = 0
    history_map = {}
    for old in state.get('history', []):
        history_map[old['id']] = old
        if not any_same_block(old, blocks):
            errors.append('Elapsed history was removed: ' + old['id'])
    windows = merge_windows(state['availability'])
    for block in blocks:
        if block['type'] == 'fixed':
            if block['refId'] not in event_ids:
                errors.append('Unknown fixed event')
            continue
        if block['type'] not in ['task', 'break']:
            errors.append('Unknown block type')
            continue
        if block['id'] in history_map:
            if not same_block(block, history_map[block['id']]):
                errors.append('Elapsed history was changed')
            continue  # Past work has already been deducted from remainingMinutes.
        fits = False
        for window in windows:
            if (read_time(window['start']) <= read_time(block['start'])
                    and read_time(block['end']) <= read_time(window['end'])):
                fits = True
        if not fits:
            errors.append('Block outside availability: ' + block['id'])
        if block['type'] == 'task':
            if block['refId'] not in task_map:
                errors.append('Unknown task')
                continue
            task = task_map[block['refId']]
            scheduled[task['id']] += duration_minutes(block['start'], block['end'])
            if task['due'] is not None and read_time(block['end']) > read_time(task['due']):
                errors.append('Task exceeds deadline: ' + task['id'])
    for task in state['tasks']:
        missing = plan['unscheduledMinutes'].get(task['id'])
        if type(missing) is not int or missing < 0:
            errors.append('Invalid unscheduled minutes: ' + task['id'])
        elif scheduled[task['id']] + missing != task['remainingMinutes']:
            errors.append('Work is not fully accounted for: ' + task['id'])
        elif missing > 0 and task['status'] != 'at_risk':
            errors.append('Unscheduled task must be at_risk: ' + task['id'])
    return errors


def same_block(first, second):
    for field in ['id', 'start', 'end', 'type', 'refId']:
        if first[field] != second[field]:
            return False
    return True


def any_same_block(block, blocks):
    for other in blocks:
        if same_block(block, other):
            return True
    return False


def compare_plans(old_plan, new_plan):
    """Match exact blocks first, then remaining blocks for the same task/event."""
    old_blocks = deepcopy(old_plan['blocks'])
    diff = []
    for block in new_plan['blocks']:
        match = None
        for old in old_blocks:
            if (old['type'] == block['type'] and old['refId'] == block['refId']
                    and old['start'] == block['start'] and old['end'] == block['end']):
                match = old
                break
        block['_exactMatch'] = match
        if match is not None:
            old_blocks.remove(match)
    for block in new_plan['blocks']:
        match = block.pop('_exactMatch')
        if match is None:
            for old in old_blocks:
                if old['type'] == block['type'] and old['refId'] == block['refId']:
                    match = old
                    old_blocks.remove(old)
                    break
        if match is None:
            status = 'added'
        elif match['start'] == block['start'] and match['end'] == block['end']:
            status = 'unchanged'
        elif duration_minutes(block['start'], block['end']) < duration_minutes(match['start'], match['end']):
            status = 'shortened'
        else:
            status = 'moved'
        block['changeStatus'] = status
        diff.append({'refId': block['refId'], 'type': block['type'],
                     'changeStatus': status, 'before': match, 'after': deepcopy(block)})
    for old in old_blocks:
        diff.append({'refId': old['refId'], 'type': old['type'],
                     'changeStatus': 'dropped', 'before': old, 'after': None})
    return diff


def deadline_risks(tasks, plan):
    result = []
    for task in tasks:
        missing = plan['unscheduledMinutes'][task['id']]
        if missing > 0:
            status = 'at_risk'
        elif task['due'] is None:
            status = 'needs_date'
        else:
            status = 'safe'
        result.append({'taskId': task['id'], 'title': task['title'],
                       'status': status, 'unscheduledMinutes': missing})
    return result


def explain_changes(diff, tasks, plan):
    counts = {'moved': 0, 'shortened': 0, 'added': 0, 'dropped': 0}
    for change in diff:
        status = change['changeStatus']
        if status in counts:
            counts[status] += 1
    parts = []
    for status in counts:
        if counts[status] > 0:
            word = ' block ' if counts[status] == 1 else ' blocks '
            parts.append(str(counts[status]) + word + status)
    message = 'The schedule is unchanged.'
    if parts:
        message = '; '.join(parts) + '.'
    for task in tasks:
        if plan['unscheduledMinutes'][task['id']] > 0:
            message += ' ' + task['title'] + ' has work that cannot fit today.'
    return message


def mock_extract(text):
    """Temporary AI stub: accepts JSON fixture text, not PDF bytes."""
    return json.loads(text)


def extract_review(text, extractor=None):
    """Extractor(text) returns {'tasks': [...]}.

    Retry invalid output once. Never automatically commit extracted tasks.
    """
    if extractor is None:
        extractor = mock_extract
    for attempt in range(2):
        try:
            data = extractor(text)
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, dict) or not isinstance(data.get('tasks'), list):
                raise ValueError('Expected an object with a tasks list')
            return {'tasks': prepare_tasks(data['tasks']), 'notices': [],
                    'requiresConfirmation': True, 'committed': False}
        except Exception:  # any AI/network/parse failure: retry, then fall back
            continue
    return {'tasks': [], 'notices': ['Extraction failed twice. No tasks were added.'],
            'requiresConfirmation': True, 'committed': False}


def mock_interpret(raw, context):
    """Small rule-based stand-in for the AI disruption interpreter."""
    match = re.search(r'\b(?:lost|lose)\s+(\d+)\s*(hours?|minutes?)\b', raw.lower())
    if match:
        minutes = int(match[1])
        if match[2].startswith('hour'):
            minutes *= 60
        return {'type': 'lost_time', 'minutes': minutes, 'raw': raw}
    if 'twice' in raw.lower() and context.get('taskId'):
        return {'type': 'task_takes_longer', 'taskId': context['taskId'], 'multiplier': 2, 'raw': raw}
    raise ValueError('Cannot understand that disruption. Use a structured disruption.')


def error_response(error):
    return {'ok': False, 'plan': None, 'violations': [str(error)], 'notices': []}

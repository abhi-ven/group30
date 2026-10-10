"""Create a daily timetable using dictionaries, lists and loops.

Read build_plan() first. It calls the smaller functions in order.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from .helpers import (DUBLIN, read_time, write_time, check_number, check_text,
                      check_choice, prepare_tasks, merge_windows, remove_interval,
                      make_block, time_order, check_plan, deadline_risks, error_response)

URGENT_HOURS = 48


def prepare_state(payload):
    """Check input and copy it, so we don't change the caller's dictionaries."""
    state = deepcopy(payload)
    state['tasks'] = prepare_tasks(state['tasks'])
    now = read_time(state['now'])
    if len(state['date']) != 10:
        raise ValueError('date must use YYYY-MM-DD')
    day_start = datetime.fromisoformat(state['date']).replace(tzinfo=DUBLIN)
    day_end = day_start + timedelta(days=1)
    day_start = day_start.astimezone(timezone.utc)
    day_end = day_end.astimezone(timezone.utc)

    events = []
    event_ids = set()
    task_ids = set()
    for task in state['tasks']:
        task_ids.add(task['id'])
    for event in state['fixedEvents']:
        check_text(event['id'], 'Event ID')
        check_text(event['title'], 'Event title')
        start = read_time(event['start'])
        end = read_time(event['end'])
        if end <= start:
            raise ValueError('Event end must be after start')
        if event['id'] in event_ids or event['id'] in task_ids:
            raise ValueError('Event IDs must be unique and different from task IDs')
        event_ids.add(event['id'])
        event.setdefault('protected', True)
        event.setdefault('source', 'manual')
        event.setdefault('kind', 'other')
        if event['protected'] is not True:
            raise ValueError('Fixed events must be protected')
        check_choice(event['source'], ['ics', 'pdf', 'paste', 'manual'], 'event source')
        check_choice(event['kind'], ['lecture', 'lab', 'meeting', 'shift', 'meal', 'sleep', 'other'], 'event kind')
        if start < day_end and end > day_start:
            events.append(event)
    state['fixedEvents'] = events

    windows = []
    for window in state['availability']:
        start = read_time(window['start'])
        end = read_time(window['end'])
        if end <= start:
            raise ValueError('Availability end must be after start')
        # Plan only inside this day and never schedule new work in the past.
        start = max(start, day_start, now)
        end = min(end, day_end)
        if start < end:
            windows.append({'start': write_time(start), 'end': write_time(end)})
    state['availability'] = merge_windows(windows)
    state.setdefault('history', [])
    return state


def task_order(task, now):
    """Urgent work (due within 48h) first by deadline; the rest by weighting."""
    if task['due'] is None:
        due = datetime.max.replace(tzinfo=timezone.utc)
    else:
        due = read_time(task['due'])
    weight = task['weighting'] or 0
    if due - now <= timedelta(hours=URGENT_HOURS):
        return (0, due, -weight, task['remainingMinutes'], task['id'])
    # A negative weight puts larger weights first when sorting ascending.
    return (1, -weight, due, task['remainingMinutes'], task['id'])


def find_free_windows(state):
    windows = deepcopy(state['availability'])
    for event in state['fixedEvents']:
        windows = remove_interval(windows, event)
    return windows


def schedule_tasks(state):
    """Place fixed events first, then fill the gaps with study and breaks."""
    blocks = deepcopy(state['history'])
    for event in state['fixedEvents']:
        blocks.append(make_block('fixed:' + event['id'], read_time(event['start']),
                                 read_time(event['end']), 'fixed', event['id']))

    now = read_time(state['now'])
    tasks = sorted(state['tasks'], key=lambda task: task_order(task, now))
    state['tasks'] = tasks
    remaining = {}
    for index in range(len(tasks)):
        task = tasks[index]
        task['priority'] = len(tasks) - index
        remaining[task['id']] = task['remainingMinutes']

    # Keep IDs unique even when a previous session has been preserved as history.
    used_ids = set()
    for block in blocks:
        used_ids.add(block['id'])
    next_id = 1
    for window in find_free_windows(state):
        current = read_time(window['start'])
        window_end = read_time(window['end'])
        while current < window_end:
            chosen_task = None
            chosen_minutes = 0
            for task in tasks:
                latest_finish = window_end
                if task['due'] is not None:
                    latest_finish = min(latest_finish, read_time(task['due']))
                space = int((latest_finish - current).total_seconds() / 60)
                amount = min(remaining[task['id']], space, 50)
                # Usually use at least 25 minutes. A final small remainder is OK.
                if amount > 0 and (amount >= 25 or amount == remaining[task['id']]):
                    chosen_task = task
                    chosen_minutes = amount
                    break
            if chosen_task is None:
                break  # Nothing fits in this gap.

            while ('study:' + str(next_id) in used_ids
                   or 'break:study:' + str(next_id) in used_ids):
                next_id += 1
            block_id = 'study:' + str(next_id)
            next_id += 1
            used_ids.add(block_id)
            finish = current + timedelta(minutes=chosen_minutes)
            blocks.append(make_block(block_id, current, finish, 'task', chosen_task['id']))
            remaining[chosen_task['id']] -= chosen_minutes
            current = finish

            if chosen_minutes == 50 and current < window_end:
                finish = min(current + timedelta(minutes=10), window_end)
                break_id = 'break:' + block_id
                blocks.append(make_block(break_id, current, finish, 'break', chosen_task['id']))
                current = finish

    warnings = []
    for task in tasks:
        if task['due'] is None:
            warnings.append(task['title'] + ': needs a date')
        if remaining[task['id']] > 0:
            task['status'] = 'at_risk'
            warnings.append(task['title'] + ': ' + str(remaining[task['id']]) + ' minutes cannot fit today before the deadline')
        elif task['remainingMinutes'] == 0:
            task['status'] = 'done'
        elif task['status'] == 'at_risk':
            task['status'] = 'todo'

    return {'id': 'plan:' + state['date'], 'date': state['date'],
            'blocks': sorted(blocks, key=time_order), 'warnings': warnings,
            'unscheduledMinutes': remaining}


def build_plan(payload):
    """Frontend entry point: input dictionary -> checked response dictionary."""
    try:
        state = prepare_state(payload)
        plan = schedule_tasks(state)
        errors = check_plan(plan, state)
        if errors:
            return {'ok': False, 'plan': None, 'violations': errors,
                    'notices': ['Correct the conflicting commitments before planning.']}
        return {'ok': True, 'plan': plan, 'state': state, 'violations': [],
                'notices': [], 'deadlineRisks': deadline_risks(state['tasks'], plan)}
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        return error_response(error)

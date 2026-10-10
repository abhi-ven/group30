"""Change the input, then reuse the same scheduler to repair the day."""
from copy import deepcopy
from datetime import timedelta
from math import ceil, isfinite
import json
from .scheduler import build_plan
from .helpers import (read_time, write_time, duration_minutes, check_number,
                      check_text, validate_task, remove_interval, compare_plans,
                      explain_changes, mock_interpret, error_response)


def validate_disruption(data):
    if not isinstance(data, dict):
        raise ValueError('Disruption must be a dictionary')
    kind = data.get('type')
    allowed = ['lost_time', 'task_takes_longer', 'urgent_task',
               'missed_session', 'cancelled_event', 'late_running_event']
    if kind not in allowed:
        raise ValueError('Unknown disruption type')
    if not isinstance(data.get('raw', ''), str):
        raise ValueError('raw must be a string')
    if kind in ['lost_time', 'late_running_event']:
        check_number(data.get('minutes'), 'minutes', 1, 1440)
    if kind == 'task_takes_longer':
        check_text(data.get('taskId'), 'taskId')
        multiplier = data.get('multiplier')
        if type(multiplier) not in (int, float) or not isfinite(multiplier) or not 1 < multiplier <= 10:
            raise ValueError('multiplier must be greater than 1 and at most 10')
    if kind == 'urgent_task':
        validate_task(data['newTask'])
    if kind == 'missed_session':
        check_text(data.get('blockId'), 'blockId')
    if kind in ['cancelled_event', 'late_running_event']:
        check_text(data.get('eventId'), 'eventId')
    return deepcopy(data)


def interpret_disruption(raw, interpreter=None, context=None):
    """interpreter(raw, context) returns JSON/dict."""
    if context is None:
        context = {}
    if interpreter is None:
        return validate_disruption(mock_interpret(raw, context)), []
    for attempt in range(2):
        try:
            data = interpreter(raw, context)
            if isinstance(data, str):
                data = json.loads(data)
            return validate_disruption(data), []
        except Exception:  # any AI/network/parse failure: retry, then fall back
            continue
    fallback = validate_disruption(mock_interpret(raw, context))
    return fallback, ['AI interpretation failed twice; rule-based fallback used.']


def find_item(items, identifier):
    for item in items:
        if item['id'] == identifier:
            return item
    raise ValueError('Unknown ID: ' + identifier)


def preserve_progress(state, old_plan, now, missed_id=None):
    """Freeze past study/break blocks and deduct only newly elapsed study.

    Prototype assumption: elapsed planned study happened unless marked missed.
    actualMinutes is not guessed; it is left unchanged.
    """
    baseline = read_time(state['now'])
    history = []
    for block in old_plan['blocks']:
        if block['type'] == 'fixed' or read_time(block['start']) >= now:
            continue
        if block['id'] == missed_id:
            continue
        past = deepcopy(block)
        end = min(read_time(block['end']), now)
        past['end'] = write_time(end)
        past['changeStatus'] = 'unchanged'
        history.append(past)
        if block['type'] == 'task':
            new_start = max(read_time(block['start']), baseline)
            elapsed = max(0, int((end - new_start).total_seconds() / 60))
            task = find_item(state['tasks'], block['refId'])
            task['remainingMinutes'] = max(0, task['remainingMinutes'] - elapsed)
    state['history'] = history


def apply_disruption(state, old_plan, disruption, now):
    kind = disruption['type']
    missed_id = None
    if kind == 'missed_session':
        missed_id = disruption['blockId']
        missed = find_item(old_plan['blocks'], missed_id)
        if missed['type'] != 'task':
            raise ValueError('Only a study session can be missed')
        if read_time(missed['start']) > now:
            raise ValueError('A future session cannot be marked missed')
        if read_time(missed['start']) < read_time(state['now']):
            raise ValueError('This session predates the last replan')
    preserve_progress(state, old_plan, now, missed_id)

    if kind == 'lost_time':
        finish = now + timedelta(minutes=disruption['minutes'])
        busy = {'start': write_time(now), 'end': write_time(finish)}
        state['availability'] = remove_interval(state['availability'], busy)
    elif kind == 'task_takes_longer':
        task = find_item(state['tasks'], disruption['taskId'])
        task['remainingMinutes'] = ceil(task['remainingMinutes'] * disruption['multiplier'])
        check_number(task['remainingMinutes'], 'remainingMinutes')
    elif kind == 'urgent_task':
        task = validate_task(disruption['newTask'])
        for existing in state['tasks']:
            if existing['id'] == task['id']:
                raise ValueError('New task ID already exists')
        state['tasks'].append(task)
    elif kind == 'missed_session':
        state['availability'] = remove_interval(state['availability'], missed)
    elif kind == 'cancelled_event':
        event = find_item(state['fixedEvents'], disruption['eventId'])
        if read_time(event['start']) < now:
            raise ValueError('Only a future event can be cancelled')
        state['fixedEvents'].remove(event)
    elif kind == 'late_running_event':
        event = find_item(state['fixedEvents'], disruption['eventId'])
        if read_time(event['end']) < now:
            raise ValueError('The event already ended before now')
        end = read_time(event['end']) + timedelta(minutes=disruption['minutes'])
        event['end'] = write_time(end)
    state['now'] = write_time(now)


def replan(previous, disruption, now, interpreter=None, context=None):
    """Pass a successful previous response, a disruption, and the current time."""
    try:
        if previous.get('ok') is not True:
            raise ValueError('A successful previous plan is required')
        state = deepcopy(previous['state'])
        old_plan = deepcopy(previous['plan'])
        current = read_time(now)
        if current < read_time(state['now']):
            raise ValueError('Cannot replan backwards in time')
        notices = []
        if isinstance(disruption, str):
            disruption, notices = interpret_disruption(disruption, interpreter, context)
        else:
            disruption = validate_disruption(disruption)
        apply_disruption(state, old_plan, disruption, current)

        # Reuse the same planner instead of writing a second scheduling algorithm.
        result = build_plan(state)
        result['notices'].extend(notices)
        if not result['ok']:
            return result
        changes = compare_plans(old_plan, result['plan'])
        result['originalPlan'] = old_plan
        result['diff'] = changes
        result['explanation'] = explain_changes(changes, result['state']['tasks'], result['plan'])
        return result
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        return error_response(error)

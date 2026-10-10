from datetime import datetime, timezone
from .helpers import read_time, duration_minutes

COLOURS = {'fixed': '#6b7280', 'task': '#2563eb', 'break': '#10b981'}


def calendar_events(result):
    state, plan = result['state'], result['plan']
    names = {t['id']: t['title'] for t in state['tasks']}
    locations = {}
    for event in state['fixedEvents']:
        names[event['id']] = event['title']
        locations[event['id']] = event.get('location', '')
    events = []
    for block in plan['blocks']:
        title = 'Break' if block['type'] == 'break' else names.get(block['refId'], block['refId'])
        events.append({'id': block['id'], 'title': title, 'start': block['start'], 'end': block['end'],
                       'type': block['type'], 'color': COLOURS[block['type']],
                       'location': locations.get(block['refId'], ''),
                       'changeStatus': block['changeStatus'],
                       'minutes': duration_minutes(block['start'], block['end'])})
    return events


def time_summary(result):
    rows = []
    history_ids = {b['id'] for b in result['state'].get('history', [])}
    for task in result['state']['tasks']:
        mine = [b for b in result['plan']['blocks'] if b['type'] == 'task'
                and b['refId'] == task['id'] and b['id'] not in history_ids]
        finish = max((read_time(b['end']) for b in mine), default=None)
        rows.append({'taskId': task['id'], 'title': task['title'], 'weighting': task['weighting'],
                     'due': task['due'], 'estimatedMinutes': task['estimatedMinutes'],
                     'estimatedHours': round(task['estimatedMinutes'] / 60, 1),
                     'scheduledMinutes': sum(duration_minutes(b['start'], b['end']) for b in mine),
                     'unscheduledMinutes': result['plan']['unscheduledMinutes'][task['id']],
                     'plannedFinish': finish.isoformat() if finish else None, 'status': task['status']})
    return rows


def to_ics(events):
    # Use the calendar library for escaping and line folding.
    from icalendar import Calendar, Event
    calendar = Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//DayShift//EN')
    for row in events:
        event = Event()
        event.add('uid', row['id'] + '@dayshift')
        event.add('dtstamp', datetime.now(timezone.utc))
        event.add('dtstart', read_time(row['start']))
        event.add('dtend', read_time(row['end']))
        event.add('summary', row['title'])
        calendar.add_component(event)
    return calendar.to_ical().decode('utf-8')

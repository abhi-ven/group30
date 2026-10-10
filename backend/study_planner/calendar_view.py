from .helpers import read_time, duration_minutes

COLOURS = {'fixed': '#6b7280', 'task': '#2563eb', 'break': '#10b981'}


def calendar_events(result):
    """Plan blocks -> events a calendar component (e.g. FullCalendar) can draw."""
    state, plan = result['state'], result['plan']
    names = {task['id']: task['title'] for task in state['tasks']}
    for event in state['fixedEvents']:
        names[event['id']] = event['title']
    events = []
    for block in plan['blocks']:
        title = 'Break' if block['type'] == 'break' else names.get(block['refId'], block['refId'])
        events.append({'id': block['id'], 'title': title,
                       'start': block['start'], 'end': block['end'],
                       'type': block['type'], 'color': COLOURS[block['type']],
                       'changeStatus': block['changeStatus'],
                       'minutes': duration_minutes(block['start'], block['end'])})
    return events


def time_summary(result):
    """Estimated and scheduled time for every task."""
    plan = result['plan']
    rows = []
    for task in result['state']['tasks']:
        mine = [b for b in plan['blocks']
                if b['type'] == 'task' and b['refId'] == task['id']]
        scheduled = sum(duration_minutes(b['start'], b['end']) for b in mine)
        finish = max((read_time(b['end']) for b in mine), default=None)
        rows.append({'taskId': task['id'], 'title': task['title'],
                     'weighting': task['weighting'], 'due': task['due'],
                     'estimatedMinutes': task['estimatedMinutes'],
                     'estimatedHours': round(task['estimatedMinutes'] / 60, 1),
                     'scheduledMinutes': scheduled,
                     'unscheduledMinutes': plan['unscheduledMinutes'][task['id']],
                     'plannedFinish': finish.isoformat() if finish else None,
                     'status': task['status']})
    return rows


def to_ics(events):
    """Export the plan as an .ics file for Google/Apple/Outlook calendars."""
    def stamp(value):
        return read_time(value).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//study-planner//EN']
    for event in events:
        lines += ['BEGIN:VEVENT', 'UID:' + event['id'] + '@study-planner',
                  'DTSTAMP:' + stamp(event['start']),
                  'DTSTART:' + stamp(event['start']),
                  'DTEND:' + stamp(event['end']),
                  'SUMMARY:' + event['title'], 'END:VEVENT']
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines)

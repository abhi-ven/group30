"""Fake student data. Extracted tasks from the PDF are added on top of these."""


def sample_task(identifier, title, minutes, due, weighting=20):
    return {'id': identifier, 'title': title, 'due': due,
            'estimatedMinutes': minutes, 'remainingMinutes': minutes,
            'actualMinutes': None, 'taskType': 'other', 'weighting': weighting,
            'source': 'manual', 'status': 'todo', 'parentId': None}


def sample_event(identifier, title, start, end, kind):
    return {'id': identifier, 'title': title,
            'start': '2026-10-10T' + start + ':00+01:00',
            'end': '2026-10-10T' + end + ':00+01:00',
            'kind': kind, 'source': 'ics', 'protected': True}


def seed_data():
    return {
        'date': '2026-10-10',
        'now': '2026-10-10T09:00:00+01:00',
        'availability': [
            {'start': '2026-10-10T09:00:00+01:00', 'end': '2026-10-10T17:00:00+01:00'}
        ],
        'fixedEvents': [
            sample_event('lecture', 'Java lecture', '11:00', '12:00', 'lecture'),
            sample_event('lunch', 'Lunch', '12:00', '13:00', 'meal'),
            sample_event('meeting', 'Group meeting', '14:00', '15:00', 'meeting')
        ],
        'tasks': [
            sample_task('lab-report', 'Complete lab report', 120, '2026-10-11T12:00:00+01:00', 40),
            sample_task('java', 'Revise Java', 60, '2026-10-12T17:00:00+01:00', 10)
        ]
    }


def print_plan(label, result):
    print('\n' + label)
    if not result['ok']:
        print(result['violations'])
        return
    for block in result['plan']['blocks']:
        print(block['start'][11:16], '-', block['end'][11:16],
              block['type'], block['refId'])
    for warning in result['plan']['warnings']:
        print('Warning:', warning)


def main():
    from .scheduler import build_plan
    from .disruptions import replan
    original = build_plan(seed_data())
    revised = replan(original, {'type': 'lost_time', 'minutes': 120},
                     now='2026-10-10T09:00:00+01:00')
    print_plan('ORIGINAL PLAN', original)
    print_plan('AFTER LOSING TWO HOURS', revised)
    if revised['ok']:
        print(revised['explanation'])


if __name__ == '__main__':
    main()

"""Convert the teammate's assignment-page records into planner tasks."""
from copy import deepcopy
from uuid import uuid4
from study_planner.helpers import validate_task
from study_planner.extractor import to_iso


def assignment_tasks(assignments):
    result = []
    for assignment in assignments:
        # Stable IDs survive reruns and subsequent disruption requests.
        assignment.setdefault('id', 'assignment:' + str(uuid4()))
        if assignment.get('plannerTask'):
            task = deepcopy(assignment['plannerTask'])
        else:
            minutes = round(float(assignment['estimated_hours']) * 60)
            module = assignment.get('module')
            title = assignment['title']
            if module:
                title += ' (' + module + ')'
            finished = assignment.get('status') in ['Done', 'Completed']
            task = {'id': assignment['id'], 'title': title, 'taskType': 'other',
                    'due': to_iso(assignment.get('deadline'), assignment.get('deadline_time')),
                    'estimatedMinutes': minutes, 'remainingMinutes': 0 if finished else minutes,
                    'weighting': assignment.get('weighting'), 'source': 'manual',
                    'status': 'done' if finished else 'todo'}
        result.append(validate_task(task))
    return result

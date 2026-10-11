import json
from .config import get_model
from .pdf_reader import parse_json
from .prompts import DISRUPTION_PROMPT


def make_context(previous):
    plan, state = previous['plan'], previous['state']
    return {'now': state['now'], 'tasks': state['tasks'],
            'studyBlocks': [b for b in plan['blocks'] if b['type'] == 'task'],
            'events': state['fixedEvents']}


def interpret(raw, context):
    reply = get_model().invoke([('system', DISRUPTION_PROMPT),
                               ('human', 'Context:\n' + json.dumps(context) + '\nMessage: ' + raw)])
    result = parse_json(reply.content)
    result['raw'] = raw
    # Validate references inside the retry operation, not only when applying it.
    for field, group in [('taskId', 'tasks'), ('eventId', 'events'), ('blockId', 'studyBlocks')]:
        if field in result and result[field] not in [x['id'] for x in context[group]]:
            raise ValueError('Model returned an unknown reference')
    return result

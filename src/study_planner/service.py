"""The frontend uses this facade for planning, extraction and disruptions."""
from datetime import datetime
from copy import deepcopy
from .calendar_view import calendar_events, time_summary, to_ics
from .config import get_model
from .disruptions import replan
from .extractor import extract_tasks
from .helpers import DUBLIN, extract_review, error_response, read_time
from .interpreter import interpret, make_context
from .pdf_reader import pdf_text
from .scheduler import build_plan


def now_iso():
    return datetime.now(DUBLIN).replace(second=0, microsecond=0).isoformat()


def _at(day, hhmm):
    return datetime.fromisoformat(f'{day}T{hhmm}').replace(tzinfo=DUBLIN).isoformat()


def new_state(day, study_start='09:00', study_end='17:00', events=None, tasks=None, now=None):
    fixed = []
    for original in events or []:
        event = deepcopy(original)
        for field in ['start', 'end']:
            # Accept our importer ISO timestamps AND the friend's HH:MM format.
            if 'T' not in event[field]:
                event[field] = _at(day, event[field])
            read_time(event[field])
        event.setdefault('kind', 'other')
        event.setdefault('source', 'manual')
        event['protected'] = True
        fixed.append(event)
    return {'date': day, 'now': now or now_iso(),
            'availability': [{'start': _at(day, study_start), 'end': _at(day, study_end)}],
            'fixedEvents': fixed, 'tasks': deepcopy(tasks or [])}


def read_assignment(pdf, extractor=None):
    try:
        text = pdf_text(pdf)
    except Exception as error:
        return {'tasks': [], 'notices': [str(error)], 'requiresConfirmation': True, 'committed': False}
    return extract_review(text, extractor=extractor or extract_tasks)


def _decorate(result):
    if result.get('ok'):
        result['calendar'] = calendar_events(result)
        result['times'] = time_summary(result)
    return result


def make_plan(state):
    return _decorate(build_plan(state))


def handle_disruption(previous, text, now=None, interpreter=None):
    if not previous or previous.get('ok') is not True:
        return error_response('Make a plan before reporting a disruption.')
    return _decorate(replan(previous, text, now=now or now_iso(),
                            interpreter=interpreter or interpret, context=make_context(previous)))


def apply_structured_disruption(previous, disruption, now=None):
    if not previous or previous.get('ok') is not True:
        return error_response('Make a plan before reporting a disruption.')
    return _decorate(replan(previous, disruption, now=now or now_iso()))


def friendly_summary(result):
    fallback = result.get('explanation') or 'Your plan is ready.'
    if not result.get('ok'):
        return fallback
    try:
        facts = {'explanation': result.get('explanation'), 'warnings': result['plan']['warnings'],
                 'times': result['times']}
        reply = get_model().invoke([('system', 'Write 2-3 friendly sentences. Use only supplied facts; never invent times or tasks.'),
                                    ('human', str(facts))])
        return reply.content.strip() or fallback
    except Exception:
        return fallback


def export_ics(result):
    return to_ics(result['calendar'])

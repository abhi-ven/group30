"""The ONLY file your Streamlit app needs to import.

    from study_planner import service

Everything here takes and returns plain dictionaries and lists, so it can be
stored in st.session_state. The AI (OpenRouter) is used in two places:
reading assignment PDFs and understanding disruptions typed in plain English.
Scheduling itself is done by the rule-based planner, never by the AI.
"""
from datetime import datetime

from .calendar_view import calendar_events, time_summary, to_ics
from .config import get_model
from .disruptions import replan
from .extractor import extract_tasks
from .helpers import DUBLIN, extract_review, error_response
from .interpreter import interpret, make_context
from .pdf_reader import pdf_text
from .scheduler import build_plan


def now_iso():
    """Current Dublin time in whole minutes."""
    return datetime.now(DUBLIN).replace(second=0, microsecond=0).isoformat()


def _at(day, hhmm):
    return f"{day}T{hhmm}:00{datetime.fromisoformat(f'{day}T{hhmm}').replace(tzinfo=DUBLIN).strftime('%z')[:3]}:00"


def new_state(day, study_start="09:00", study_end="17:00", events=None,
              tasks=None, now=None):
    """Build the planner input.

    day:    'YYYY-MM-DD'
    events: [{'id': 'lec1', 'title': 'Java lecture', 'start': '11:00',
              'end': '12:00', 'kind': 'lecture'}, ...]   (HH:MM, Dublin time)
    tasks:  confirmed tasks, e.g. from read_assignment()['tasks']
    """
    fixed = []
    for event in events or []:
        fixed.append({'id': event['id'], 'title': event['title'],
                      'start': _at(day, event['start']), 'end': _at(day, event['end']),
                      'kind': event.get('kind', 'other'),
                      'source': event.get('source', 'manual'), 'protected': True})
    return {'date': day, 'now': now or now_iso(),
            'availability': [{'start': _at(day, study_start), 'end': _at(day, study_end)}],
            'fixedEvents': fixed, 'tasks': list(tasks or [])}


def read_assignment(pdf, extractor=None):
    """AI step 1: PDF -> proposed tasks for the user to review and edit.

    Returns {'tasks': [...], 'notices': [...], 'requiresConfirmation': True}.
    Nothing is scheduled until you pass the confirmed tasks to new_state().
    """
    try:
        text = pdf_text(pdf)
    except Exception as error:  # unreadable or scanned PDF
        return {'tasks': [], 'notices': [str(error)],
                'requiresConfirmation': True, 'committed': False}
    return extract_review(text, extractor=extractor or extract_tasks)


def _decorate(result):
    if result.get('ok'):
        result['calendar'] = calendar_events(result)
        result['times'] = time_summary(result)
    return result


def make_plan(state):
    """Build the day's plan. Adds 'calendar' and 'times' for the frontend."""
    return _decorate(build_plan(state))


def handle_disruption(previous, text, now=None, interpreter=None):
    """AI step 2: plain-English disruption -> repaired plan.

    previous: the last successful result from make_plan / handle_disruption.
    text:     e.g. 'I lost 2 hours' or 'lab report will take twice as long'.
    Falls back to a simple rule-based reader if the AI fails twice.
    """
    if not previous or previous.get('ok') is not True:
        return error_response('Make a plan before reporting a disruption.')
    result = replan(previous, text, now=now or now_iso(),
                    interpreter=interpreter or interpret,
                    context=make_context(previous))
    return _decorate(result)


def apply_structured_disruption(previous, disruption, now=None):
    """Same as handle_disruption but for buttons/forms, with no AI involved.
    e.g. {'type': 'lost_time', 'minutes': 120}"""
    if not previous or previous.get('ok') is not True:
        return error_response('Make a plan before reporting a disruption.')
    return _decorate(replan(previous, disruption, now=now or now_iso()))


def friendly_summary(result):
    """Optional AI step 3: short plain-English summary of the plan.
    Presentation only. Falls back to the rule-based text if the AI fails."""
    fallback = result.get('explanation') or 'Your plan is ready.'
    if not result.get('ok'):
        return fallback
    try:
        facts = {'explanation': result.get('explanation'),
                 'warnings': result['plan']['warnings'],
                 'times': [{k: row[k] for k in ('title', 'estimatedHours',
                            'scheduledMinutes', 'unscheduledMinutes')}
                           for row in result['times']]}
        reply = get_model().invoke([
            ('system', 'Write 2-3 friendly sentences summarising this study '
                       'plan for a student. Use only the facts given. Do not '
                       'invent times or tasks.'),
            ('human', str(facts))])
        text = reply.content.strip()
        return text or fallback
    except Exception:
        return fallback


def export_ics(result):
    """Calendar file text for st.download_button."""
    return to_ics(result['calendar'])

"""Read a Google/Outlook .ics timetable into the scheduler's fixedEvents.

The calendar libraries parse the file and expand repeating classes. Our code
only converts each occurrence into an ordinary dictionary. No AI or network.
"""
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from zoneinfo import ZoneInfo
DUBLIN = ZoneInfo('Europe/Dublin')


def write_time(value):
    return value.astimezone(DUBLIN).isoformat()


def time_order(event):
    return datetime.fromisoformat(event['start']).astimezone(timezone.utc)


def check_minute(value):
    if value.second or value.microsecond:
        raise ValueError('Calendar times must use whole minutes')


def calendar_time(value, calendar_zone):
    # All-day entries become full-day protected commitments.
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=calendar_zone)
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min, calendar_zone)
    raise ValueError('Calendar entry has an invalid date/time')


def fix_date_only_until(calendar, calendar_zone):
    """Google's supplied timetable uses UNTIL=YYYYMMDD with timed events.

    Some recurrence libraries reject this combination. Interpret this date as
    inclusive through the end of that local day, without editing the source file.
    """
    changed = False
    for event in calendar.walk('VEVENT'):
        rule = event.get('RRULE')
        start = event.get('DTSTART')
        if rule is None or start is None or not isinstance(start.dt, datetime):
            continue
        until_values = rule.get('UNTIL', [])
        if until_values and type(until_values[0]) is date:
            start_time = calendar_time(start.dt, calendar_zone)
            last_day = until_values[0]
            inclusive_end = datetime.combine(last_day, time(23, 59, 59), start_time.tzinfo)
            rule['UNTIL'] = [inclusive_end.astimezone(timezone.utc)]
            changed = True
    return changed


def import_semester(ics_text, semester_start, semester_end):
    """Import all classes between inclusive semester dates, as ISO dictionaries.

    AI agents can read the returned fixedEvents. No assignment intake/scheduling.
    """
    try:
        # Lazy imports let the original seeded demo run without calendar packages.
        from icalendar import Calendar
        import recurring_ical_events
        first_day = date.fromisoformat(semester_start)
        last_day = date.fromisoformat(semester_end)
        if len(semester_start) != 10 or len(semester_end) != 10:
            raise ValueError('Use YYYY-MM-DD for semester dates')
        if last_day < first_day:
            raise ValueError('Semester end must be on or after the start')
        if (last_day - first_day).days > 200:
            raise ValueError('Select one semester, at most 201 calendar days')
        if isinstance(ics_text, bytes):
            ics_text = ics_text.decode('utf-8-sig')
        if not isinstance(ics_text, str) or 'BEGIN:VCALENDAR' not in ics_text:
            raise ValueError('Upload an .ics calendar file')
        if len(ics_text.encode('utf-8')) > 2 * 1024 * 1024:
            raise ValueError('Calendar file must be under 2 MB')
        calendar = Calendar.from_ical(ics_text)
        if calendar.name != 'VCALENDAR':
            raise ValueError('Expected one VCALENDAR')
        calendar_zone = ZoneInfo(str(calendar.get('X-WR-TIMEZONE', 'Europe/Dublin')))
        notices = []
        if fix_date_only_until(calendar, calendar_zone):
            notices.append('Date-only recurrence end dates were treated as inclusive local dates.')

        # Floating times need an explicit timezone before recurrence expansion.
        floating = False
        for event in calendar.walk('VEVENT'):
            for field in ['DTSTART', 'DTEND', 'RECURRENCE-ID']:
                value = event.get(field)
                if value is not None and isinstance(value.dt, datetime) and value.dt.tzinfo is None:
                    event[field].dt = value.dt.replace(tzinfo=calendar_zone)
                    floating = True
        if floating:
            notices.append('Times without offsets use the calendar timezone: ' + str(calendar_zone))

        start_of_day = datetime.combine(first_day, time.min, DUBLIN)
        end_of_day = datetime.combine(last_day + timedelta(days=1), time.min, DUBLIN)
        occurrences = recurring_ical_events.of(calendar).between(start_of_day, end_of_day)
        events = []
        seen = {}
        for occurrence in occurrences:
            if str(occurrence.get('STATUS', '')).upper() == 'CANCELLED':
                continue
            if str(occurrence.get('TRANSP', 'OPAQUE')).upper() == 'TRANSPARENT':
                continue  # An event marked free does not occupy study time.
            start_value = occurrence.get('DTSTART')
            end_value = occurrence.get('DTEND')
            if start_value is None or end_value is None:
                raise ValueError('A calendar occurrence has no start or end time')
            start = calendar_time(start_value.dt, calendar_zone).astimezone(timezone.utc)
            end = calendar_time(end_value.dt, calendar_zone).astimezone(timezone.utc)
            if end <= start:
                raise ValueError('Calendar event end must be after its start')
            if start >= end_of_day.astimezone(timezone.utc) or end <= start_of_day.astimezone(timezone.utc):
                continue
            # The existing scheduler requires whole-minute timestamps.
            check_minute(start)
            check_minute(end)
            uid = str(occurrence.get('UID', ''))
            if not uid:
                raise ValueError('Calendar event is missing its UID')
            original_start = occurrence.get('RECURRENCE-ID')
            identity_time = start
            if original_start is not None:
                identity_time = calendar_time(original_start.dt, calendar_zone).astimezone(timezone.utc)
            # UID identifies the series; original time distinguishes each session.
            identifier = 'ics:' + sha256((uid + '|' + identity_time.isoformat()).encode()).hexdigest()[:24]
            title = str(occurrence.get('SUMMARY', 'Untitled calendar event'))
            if not title.strip():
                title = 'Untitled calendar event'
            kind = 'other'
            if 'lecture' in title.lower():
                kind = 'lecture'
            elif 'lab' in title.lower() or 'practical' in title.lower():
                kind = 'lab'
            event = {'id': identifier, 'title': title, 'start': write_time(start),
                     'end': write_time(end), 'source': 'ics', 'kind': kind,
                     'protected': True, 'location': str(occurrence.get('LOCATION', ''))}
            if identifier in seen:
                if event != seen[identifier]:
                    raise ValueError('Conflicting calendar occurrences share an ID')
                continue
            seen[identifier] = event
            events.append(event)
        events = sorted(events, key=time_order)
        if not events:
            notices.append('No classes found in the selected semester dates.')
        return {'ok': True, 'calendarName': str(calendar.get('X-WR-CALNAME', 'Imported timetable')),
                'semesterStart': semester_start, 'semesterEnd': semester_end,
                'fixedEvents': events,
                'notices': notices, 'violations': []}
    except ImportError:
        return {'ok': False, 'fixedEvents': [], 'notices': [],
                'violations': ['Install calendar packages: python3 -m pip install -r requirements.txt']}
    except Exception as error:
        # A library parse/recurrence failure must never return a partial timetable.
        return {'ok': False, 'fixedEvents': [], 'notices': [],
                'violations': ['Calendar import failed: ' + str(error)]}



def events_for_day(timetable, selected_day):
    """Include cross-midnight commitments touching this local day."""
    day = date.fromisoformat(selected_day)
    start = datetime.combine(day, time.min, DUBLIN).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time.min, DUBLIN).astimezone(timezone.utc)
    result = []
    for event in timetable['fixedEvents']:
        if time_order(event) < end and datetime.fromisoformat(event['end']).astimezone(timezone.utc) > start:
            result.append(event.copy())
    return result

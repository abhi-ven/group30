import os
import tempfile
import unittest
from unittest.mock import patch
from calendar_import import import_semester, events_for_day
from timetable_store import save_timetable, load_timetable, delete_timetable


def calendar(events):
    return ('BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//DayShift synthetic tests//EN\n'
            'X-WR-TIMEZONE:Europe/Dublin\nX-WR-CALNAME:Test timetable\n'
            + events + 'END:VCALENDAR\n')


def event(uid, start, end, extra='', title='Example Lecture'):
    return ('BEGIN:VEVENT\nUID:' + uid + '\nSUMMARY:' + title + '\n'
            'DTSTART' + start + '\nDTEND' + end + '\n'
            + extra + 'END:VEVENT\n')


class CalendarTests(unittest.TestCase):
    def test_weekly_recurring_classes_and_clock_change(self):
        text = calendar(event('weekly', ';TZID=Europe/Dublin:20261019T090000',
                              ';TZID=Europe/Dublin:20261019T095000', 'RRULE:FREQ=WEEKLY;COUNT=3\n'))
        result = import_semester(text, '2026-10-19', '2026-11-02')
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(result['fixedEvents']), 3)
        self.assertEqual(result['fixedEvents'][0]['start'], '2026-10-19T09:00:00+01:00')
        self.assertEqual(result['fixedEvents'][1]['start'], '2026-10-26T09:00:00+00:00')
        self.assertEqual(len(events_for_day(result, '2026-10-26')), 1)

    def test_google_date_only_until_includes_last_day(self):
        text = calendar(event('google', ';TZID=Europe/Dublin:20261005T090000',
                              ';TZID=Europe/Dublin:20261005T095000', 'RRULE:FREQ=WEEKLY;UNTIL=20261019;BYDAY=MO\n'))
        result = import_semester(text, '2026-10-05', '2026-10-19')
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(result['fixedEvents']), 3)
        self.assertTrue(result['notices'])

    def test_excluded_occurrence(self):
        text = calendar(event('exclude', ';TZID=Europe/Dublin:20261005T090000',
                              ';TZID=Europe/Dublin:20261005T095000',
                              'RRULE:FREQ=WEEKLY;COUNT=3\nEXDATE;TZID=Europe/Dublin:20261012T090000\n'))
        result = import_semester(text, '2026-10-05', '2026-10-19')
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(result['fixedEvents']), 2)
        self.assertEqual(events_for_day(result, '2026-10-12'), [])

    def test_moved_occurrence(self):
        base = event('moved', ';TZID=Europe/Dublin:20261005T090000',
                     ';TZID=Europe/Dublin:20261005T095000', 'RRULE:FREQ=WEEKLY;COUNT=2\n')
        change = event('moved', ';TZID=Europe/Dublin:20261012T110000',
                       ';TZID=Europe/Dublin:20261012T115000',
                       'RECURRENCE-ID;TZID=Europe/Dublin:20261012T090000\n')
        result = import_semester(calendar(base + change), '2026-10-05', '2026-10-12')
        self.assertTrue(result['ok'], result)
        self.assertEqual(events_for_day(result, '2026-10-12')[0]['start'][11:16], '11:00')
        self.assertEqual(len(result['fixedEvents']), 2)

    def test_utc_conversion_and_stable_ids(self):
        text = calendar(event('utc', ':20261012T080000Z', ':20261012T085000Z'))
        first = import_semester(text, '2026-10-12', '2026-10-12')
        second = import_semester(text, '2026-10-12', '2026-10-12')
        self.assertEqual(first['fixedEvents'], second['fixedEvents'])
        self.assertEqual(first['fixedEvents'][0]['start'][11:16], '09:00')
        self.assertTrue(first['fixedEvents'][0]['protected'])

    def test_distinct_calendar_entries_are_preserved(self):
        text = calendar(event('a', ':20261012T080000Z', ':20261012T090000Z')
                        + event('b', ':20261012T083000Z', ':20261012T093000Z', title='Other Lab'))
        result = import_semester(text, '2026-10-12', '2026-10-12')
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(result['fixedEvents']), 2)
        self.assertNotIn('overlaps', result)

    def test_cancelled_and_free_entries_do_not_block_time(self):
        text = calendar(event('cancel', ':20261012T080000Z', ':20261012T090000Z', 'STATUS:CANCELLED\n')
                        + event('free', ':20261012T100000Z', ':20261012T110000Z', 'TRANSP:TRANSPARENT\n'))
        result = import_semester(text, '2026-10-12', '2026-10-12')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['fixedEvents'], [])

    def test_floating_time_uses_calendar_timezone(self):
        text = calendar(event('floating', ':20261012T090000', ':20261012T095000'))
        result = import_semester(text, '2026-10-12', '2026-10-12')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['fixedEvents'][0]['start'], '2026-10-12T09:00:00+01:00')
        self.assertTrue(result['notices'])

    def test_all_day_and_cross_midnight(self):
        text = calendar(event('holiday', ';VALUE=DATE:20261012', ';VALUE=DATE:20261013')
                        + event('night', ':20261011T223000Z', ':20261012T003000Z'))
        result = import_semester(text, '2026-10-12', '2026-10-12')
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(result['fixedEvents']), 2)
        self.assertEqual(len(events_for_day(result, '2026-10-12')), 2)

    def test_invalid_input_and_range(self):
        self.assertFalse(import_semester('not a calendar', '2026-10-12', '2026-10-12')['ok'])
        self.assertFalse(import_semester(calendar(''), '2026-10-12', '2026-09-12')['ok'])
        self.assertFalse(import_semester(calendar(''), '2026-01-01', '2027-01-01')['ok'])

    def test_storage_survives_reload_and_can_be_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {'TIMETABLE_DATA_DIR': folder}):
                imported = import_semester(calendar(event('save', ':20261012T080000Z', ':20261012T090000Z')),
                                           '2026-10-12', '2026-10-12')
                record = save_timetable(imported)
                self.assertEqual(load_timetable(record['id']), record)
                delete_timetable(record['id'])
                with self.assertRaises(FileNotFoundError):
                    load_timetable(record['id'])
                with self.assertRaises(ValueError):
                    load_timetable('../arbitrary-file')


if __name__ == '__main__':
    unittest.main()

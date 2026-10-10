"""Run with: python3 -m unittest discover -s tests -v"""
import json
import unittest
from copy import deepcopy
from backend import build_plan, replan, seed_data, extract_review
from backend.demo import sample_task
from backend.helpers import check_plan, read_time

NOW = '2026-10-10T09:00:00+01:00'


class BackendTests(unittest.TestCase):
    def normal_plan(self):
        result = build_plan(seed_data())
        self.assertTrue(result['ok'], result)
        return result

    def test_normal_day(self):
        result = self.normal_plan()
        self.assertEqual(sum(result['plan']['unscheduledMinutes'].values()), 0)
        self.assertEqual(result['violations'], [])

    def test_lost_time_preserves_fixed_events(self):
        original = self.normal_plan()
        revised = replan(original, {'type': 'lost_time', 'minutes': 120}, NOW)
        self.assertTrue(revised['ok'], revised)
        for old in original['plan']['blocks']:
            if old['type'] == 'fixed':
                self.assertIn(old, revised['plan']['blocks'])
        for block in revised['plan']['blocks']:
            if block['type'] == 'task':
                self.assertGreaterEqual(read_time(block['start']), read_time('2026-10-10T11:00:00+01:00'))
        self.assertTrue(revised['explanation'])

    def test_urgent_task_is_first(self):
        urgent = sample_task('urgent', 'Urgent assignment', 60, '2026-10-10T11:00:00+01:00')
        revised = replan(self.normal_plan(), {'type': 'urgent_task', 'newTask': urgent}, NOW)
        self.assertTrue(revised['ok'], revised)
        for block in revised['plan']['blocks']:
            if block['type'] == 'task':
                self.assertEqual(block['refId'], 'urgent')
                break

    def test_impossible_day_is_flagged(self):
        data = seed_data()
        data['tasks'][0]['remainingMinutes'] = 1000
        result = build_plan(data)
        self.assertTrue(result['ok'], result)
        self.assertGreater(result['plan']['unscheduledMinutes']['lab-report'], 0)
        self.assertEqual(result['state']['tasks'][0]['status'], 'at_risk')

    def test_task_does_not_finish_after_deadline(self):
        data = seed_data()
        data['tasks'] = [sample_task('urgent', 'Due soon', 120, '2026-10-10T09:30:00+01:00')]
        result = build_plan(data)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['plan']['unscheduledMinutes']['urgent'], 90)
        for block in result['plan']['blocks']:
            if block['type'] == 'task':
                self.assertLessEqual(read_time(block['end']), read_time(data['tasks'][0]['due']))

    def test_missing_deadline_stays_null(self):
        data = seed_data()
        data['tasks'][0]['due'] = None
        result = build_plan(data)
        self.assertTrue(result['ok'], result)
        for task in result['state']['tasks']:
            if task['id'] == 'lab-report':
                self.assertIsNone(task['due'])
        self.assertTrue(any('needs a date' in message for message in result['plan']['warnings']))

    def test_duplicate_tasks_merge(self):
        data = seed_data()
        duplicate = deepcopy(data['tasks'][0])
        duplicate['id'] = 'duplicate'
        data['tasks'].append(duplicate)
        result = build_plan(data)
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(result['state']['tasks']), 2)

    def test_extraction_requires_confirmation(self):
        text = json.dumps({'tasks': seed_data()['tasks']})
        result = extract_review(text)
        self.assertEqual(len(result['tasks']), 2)
        self.assertTrue(result['requiresConfirmation'])
        self.assertFalse(result['committed'])

    def test_minimal_ai_output_gets_id_and_remaining_work(self):
        text = json.dumps({'tasks': [{'title': 'Essay', 'estimatedMinutes': 120}]})
        review = extract_review(text)
        task = review['tasks'][0]
        self.assertTrue(task['id'])
        self.assertEqual(task['remainingMinutes'], 120)
        self.assertNotIn('sourceSnippet', task)
        self.assertNotIn('confidence', task)
        data = seed_data()
        data['tasks'] = review['tasks']
        original = build_plan(data)
        revised = replan(original, {'type': 'lost_time', 'minutes': 10}, NOW)
        self.assertTrue(revised['ok'], revised)
        self.assertEqual(revised['state']['tasks'][0]['id'], task['id'])

    def test_removed_metadata_is_not_returned(self):
        data = seed_data()
        data['tasks'][0]['sourceSnippet'] = 'Old extractor text'
        data['tasks'][0]['confidence'] = 'high'
        result = build_plan(data)
        self.assertTrue(result['ok'], result)
        for task in result['state']['tasks']:
            self.assertNotIn('sourceSnippet', task)
            self.assertNotIn('confidence', task)

    def test_malformed_extraction_retries_once(self):
        calls = []
        def broken_extractor(text):
            calls.append(text)
            return '{bad json'
        result = extract_review('PDF text', broken_extractor)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result['tasks'], [])
        self.assertTrue(result['notices'])

    def test_malformed_interpretation_uses_fallback(self):
        calls = []
        def broken_interpreter(raw, context):
            calls.append(raw)
            return {'type': 'lost_time', 'minutes': -1}
        result = replan(self.normal_plan(), 'I lost 2 hours', NOW,
                        interpreter=broken_interpreter)
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(calls), 2)
        self.assertTrue(result['notices'])

    def test_unknown_text_does_not_guess(self):
        result = replan(self.normal_plan(), 'Something happened', NOW)
        self.assertFalse(result['ok'])
        self.assertIsNone(result['plan'])

    def test_overlapping_fixed_events_return_error(self):
        data = seed_data()
        data['fixedEvents'][1]['start'] = '2026-10-10T11:30:00+01:00'
        result = build_plan(data)
        self.assertFalse(result['ok'])
        self.assertIsNone(result['plan'])

    def test_task_takes_longer(self):
        result = replan(self.normal_plan(), {'type': 'task_takes_longer',
                        'taskId': 'lab-report', 'multiplier': 2}, NOW)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['state']['tasks'][0]['remainingMinutes'], 240)

    def test_cancelled_event(self):
        result = replan(self.normal_plan(), {'type': 'cancelled_event', 'eventId': 'meeting'}, NOW)
        self.assertTrue(result['ok'], result)
        for block in result['plan']['blocks']:
            self.assertNotEqual(block['refId'], 'meeting')
        self.assertTrue(any(row['changeStatus'] == 'dropped' and row['refId'] == 'meeting' for row in result['diff']))

    def test_late_running_event_and_conflict(self):
        result = replan(self.normal_plan(), {'type': 'late_running_event', 'eventId': 'meeting', 'minutes': 30}, NOW)
        self.assertTrue(result['ok'], result)
        for block in result['plan']['blocks']:
            if block['refId'] == 'meeting':
                self.assertEqual(block['end'], '2026-10-10T15:30:00+01:00')
        conflict = replan(self.normal_plan(), {'type': 'late_running_event', 'eventId': 'lecture', 'minutes': 30}, NOW)
        self.assertFalse(conflict['ok'])

    def test_missed_session_keeps_work_remaining(self):
        original = self.normal_plan()
        block = original['plan']['blocks'][0]
        self.assertEqual(block['type'], 'task')
        result = replan(original, {'type': 'missed_session', 'blockId': block['id']}, block['end'])
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['state']['tasks'][0]['remainingMinutes'], 120)

    def test_replanning_does_not_deduct_progress_twice(self):
        time = '2026-10-10T09:30:00+01:00'
        result = replan(self.normal_plan(), {'type': 'lost_time', 'minutes': 10}, time)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['state']['tasks'][0]['remainingMinutes'], 90)
        again = replan(result, {'type': 'lost_time', 'minutes': 10}, time)
        self.assertTrue(again['ok'], again)
        self.assertEqual(again['state']['tasks'][0]['remainingMinutes'], 90)
        self.assertEqual(again['plan']['blocks'][0]['end'], time)

    def test_missed_session_preserves_elapsed_break_without_id_collision(self):
        original = self.normal_plan()
        block = original['plan']['blocks'][0]
        result = replan(original, {'type': 'missed_session', 'blockId': block['id']},
                        '2026-10-10T10:00:00+01:00')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['state']['tasks'][0]['remainingMinutes'], 120)
        self.assertEqual(result['plan']['blocks'][0]['type'], 'break')

    def test_inputs_are_not_changed(self):
        data = seed_data()
        before = deepcopy(data)
        build_plan(data)
        self.assertEqual(data, before)
        original = self.normal_plan()
        before = deepcopy(original)
        replan(original, {'type': 'lost_time', 'minutes': 120}, NOW)
        self.assertEqual(original, before)

    def test_invalid_inputs(self):
        for bad in [0, -1, True, 2.5, '50']:
            data = seed_data()
            data['tasks'][0]['estimatedMinutes'] = bad
            self.assertFalse(build_plan(data)['ok'])
        data = seed_data()
        data['now'] = '2026-10-10T09:00:00'
        self.assertFalse(build_plan(data)['ok'])
        result = replan(self.normal_plan(), {'type': 'lost_time', 'minutes': -1}, NOW)
        self.assertFalse(result['ok'])

    def test_overlapping_availability_is_not_counted_twice(self):
        data = seed_data()
        data['availability'] *= 2
        self.assertEqual(build_plan(data)['plan'], self.normal_plan()['plan'])

    def test_checker_detects_deleted_fixed_event(self):
        result = self.normal_plan()
        for block in result['plan']['blocks']:
            if block['type'] == 'fixed':
                result['plan']['blocks'].remove(block)
                break
        self.assertTrue(check_plan(result['plan'], result['state']))

    def test_clock_change_uses_real_elapsed_time(self):
        data = {'date': '2026-10-25', 'now': '2026-10-25T01:00:00+01:00',
                'fixedEvents': [], 'availability': [
                    {'start': '2026-10-25T01:00:00+01:00', 'end': '2026-10-25T02:00:00+00:00'}],
                'tasks': [sample_task('clock', 'Clock change', 100, None)]}
        result = build_plan(data)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['plan']['unscheduledMinutes']['clock'], 0)


if __name__ == '__main__':
    unittest.main()

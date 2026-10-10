import unittest
from pathlib import Path
from datetime import date
from icalendar import Calendar
from assignment_bridge import assignment_tasks
from study_planner import service

DAY='2026-10-12'
def at(clock): return service._at(DAY,clock)
class IntegrationTests(unittest.TestCase):
    def plan(self):
        tasks=assignment_tasks([{'title':'Report, final','deadline':'2026-10-20','estimated_hours':3,'weighting':40}])
        return service.make_plan(service.new_state(DAY,events=[{'id':'lecture','title':'Java',
            'start':at('10:00'),'end':at('11:00'),'source':'ics','kind':'lecture'}],tasks=tasks,now=at('09:00')))
    def test_ids(self):
        rows=[{'title':'Essay','estimated_hours':2,'deadline':'2026-10-20'}]
        a,b=assignment_tasks(rows),assignment_tasks(rows)
        self.assertEqual(a[0]['id'],b[0]['id']);self.assertEqual(a[0]['remainingMinutes'],120)
    def test_six_disruptions(self):
        p=self.plan();self.assertTrue(p['ok'],p);tid=p['state']['tasks'][0]['id']
        cases=[({'type':'lost_time','minutes':30},'09:00'),
          ({'type':'task_takes_longer','taskId':tid,'multiplier':2},'09:00'),
          ({'type':'urgent_task','newTask':{'title':'Urgent','estimatedMinutes':30,'due':at('16:00'),'weighting':50}},'09:00'),
          ({'type':'missed_session','blockId':'study:1'},'09:50'),
          ({'type':'cancelled_event','eventId':'lecture'},'09:00'),
          ({'type':'late_running_event','eventId':'lecture','minutes':30},'11:20')]
        for change,clock in cases:
            with self.subTest(change=change):
                r=service.apply_structured_disruption(p,change,now=at(clock));self.assertTrue(r['ok'],r)
                if change['type']=='late_running_event':
                    self.assertEqual(r['state']['tasks'][0]['remainingMinutes'],130)
                    for b in r['calendar']:
                        if b['type']=='task':self.assertFalse(b['start']<at('11:30') and b['end']>at('11:00'))
    def test_fallback(self):
        def fail(*args):raise RuntimeError('offline')
        r=service.handle_disruption(self.plan(),'I lost 2 hours',now=at('09:00'),interpreter=fail)
        self.assertTrue(r['ok'],r);self.assertTrue(r['notices'])
    def test_weighting(self):
        tasks=assignment_tasks([{'title':t,'estimated_hours':1,'deadline':'2026-10-20','weighting':w} for t,w in [('Low',10),('High',60)]])
        r=service.make_plan(service.new_state(DAY,tasks=tasks,now=at('09:00')))
        self.assertEqual(next(b for b in r['calendar'] if b['type']=='task')['title'],'High')
    def test_export(self):
        c=Calendar.from_ical(service.export_ics(self.plan()))
        self.assertTrue(any(str(e.get('summary'))=='Report, final' for e in c.walk('VEVENT')))
    def test_daily_budget(self):
        p=self.plan();state=p['state'];state['studyMinuteLimit']=60
        r=service.make_plan(state)
        self.assertTrue(r['ok'],r)
        self.assertEqual(sum(b['minutes'] for b in r['calendar'] if b['type']=='task'),60)

    def test_ui(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'),default_timeout=15)
        app.session_state['semester_timetable']={'id':'test','semesterStart':DAY,'semesterEnd':'2026-10-20',
          'fixedEvents':[{'id':'lecture','title':'Java','start':at('10:00'),'end':at('11:00'),'kind':'lecture','source':'ics','protected':True}]}
        app.session_state['class_day_test']=date.fromisoformat(DAY)
        app.run();self.assertFalse(app.exception)
        app.switch_page('assignments.py').run()
        next(b for b in app.button if b.label=='Load demo assignments').click().run()
        app.switch_page('planner.py').run()
        next(b for b in app.button if b.label=='Plan my study time').click().run()
        self.assertFalse(app.exception);self.assertTrue(app.session_state['day_plans'][DAY]['ok'])
        next(b for b in app.button if b.label=='→').click().run()
        self.assertEqual(app.session_state['calendar_selected_day'],'2026-10-13')
        app.switch_page('dashboard.py').run()
        self.assertFalse(app.exception)
        next(b for b in app.button if b.label=='I lost two hours').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_area[0].value,'I lost 2 hours')
        app.switch_page('rescue.py').run()
        from unittest.mock import patch
        with patch('study_planner.interpreter.get_model',side_effect=RuntimeError('offline')):
            next(b for b in app.button if b.label=='Rescue my day').click().run()
        self.assertFalse(app.exception)
        self.assertIn('diff',app.session_state['day_plans'][DAY])
        self.assertEqual(app.session_state['state']['plan'],app.session_state['day_plans'][DAY]['plan'])

# DayShift — Full Team App

A functioning four-page Streamlit app combining the team's frontend, semester calendar importer, assignment input and AI/planning service. Dashboard and Rescue My Day use the real generated plan rather than a separate sample plan.

1. Open **My Timetable** in the sidebar. Upload your `.ics` file and choose semester dates.
2. Open **Assignments**. Load demo assignments or enter your own. Add grade weighting when you know it.
3. Return to **My Timetable**. Use the day arrows, set available study times and maximum study hours, then click **Plan my study time**.
4. Open **Dashboard** to see the generated plan and assignment deadlines.
5. Open **Rescue My Day** in the sidebar. Describe what changed and submit. Your updated plan appears across the schedule pages.
Rescue My Day has its own sidebar page. Enter your message and submit it once. Optional weekly lectures and work shifts can be added below the imported timetable. Export the selected plan as an `.ics` file from My Timetable.

## Enable the AI

Copy `.env.example` to `.env`, enter the key and desired available model, then restart Streamlit:

```text
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```
The AI converts the student's message into structured changes. The rule-based scheduler chooses the actual new times, preserves elapsed progress and returns a diff. It supports lost time, longer work, urgent tasks, missed sessions, cancelled commitments and late events.

Work due within 48 hours is prioritised by deadline; other work is prioritised by weighting. Study fills free gaps, up to 50 minutes per session with breaks, and respects the daily study-time cap.

## Main files

- `app.py`: Registers four pages and shows a sidebar divider below Dashboard.
- `app_state.py`: Shared plan storage and adapter between frontend `fixed_events` and planner `fixedEvents`.
- `dashboard.py`: Generated timeline, deadline cards and a link to My Timetable.
- `planner.py`: Imported daily classes, day arrows, weekly commitments, study availability, planning and export.
- `assignments.py` / `assignments_page.py`: Demo and manual assignments and optional PDF review.
- `rescue.py`: Reusable disruption component and before/after view, shown by `rescue_page.py`.
- `components.py`, `styles.py`, `helper_functions.py`: Reusable UI components, styling and helper functions with escaped text and Dublin-aware timestamps. No shadcn package is needed for these components.
- `calendar_import.py`, `timetable_store.py`, `timetable_ui.py`: Recurring semester imports, saved calendar and day view.
- `assignment_bridge.py`: Stable generated IDs, total hours converted to minutes, deadlines and weighting.
- `study_planner/`: Scheduling service, scheduler, interpreter, PDF extraction, validation and calendar export.

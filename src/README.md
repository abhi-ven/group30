# DayShift — full team app

A functioning four-page Streamlit app combining the team's frontend, semester calendar importer, assignment input and friend's AI/planning service. Dashboard and Rescue My Day use the real generated plan, rather than a separate sample plan.

## Run in VS Code

Use Python 3.11 or newer. Unzip and open the `dayshift-team-app` folder, then use its terminal:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

On Windows, use `python` if needed. Run **app.py**, not individual page files.

## Try it step by step

1. Open **My Timetable** in the sidebar. Upload your `.ics` file and choose semester dates.
2. Open **Assignments**. Load demo assignments or enter your own. Add grade weighting when you know it.
3. Return to **My Timetable**. Use the day arrows, set available study times and max study hours, then click **Plan my study time**.
4. Open **Dashboard** to see that plan and assignment deadlines.
5. Open **Rescue My Day** in the sidebar. Describe what changed and submit. Your updated plan appears on all three schedule pages.
6. Without an AI key, expand **Report a change using a form** to demonstrate any of the six disruptions. Choose a report time appropriate to the event/session. Future sessions cannot be marked missed; events that have not started cannot be reported late; cancellation is for future events.

Rescue My Day has its own sidebar page; enter your message and submit it once. Optional weekly lectures/work shifts can be added below the imported timetable. Export the selected plan as an `.ics` file from My Timetable.

## Enable the friend's AI

Copy `.env.example` to `.env`, enter the key and desired available model, then restart Streamlit:

```text
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```

The old names `ai_api_key` / `ai_model` also work. Never commit `.env`. Live model calls were not tested here; use a model available to your account.

Without a key, timetable imports, assignments, planning and structured disruption forms work. Simple **I lost 2 hours** messages use the fallback. General natural-language interpretation and optional PDF extraction need AI. Proposed PDF tasks are only added after acceptance.

The AI converts the student's message into structured changes. Your friend's rule-based scheduler chooses the actual new times, preserves elapsed progress and returns a diff. It supports lost time, longer work, urgent tasks, missed sessions, cancelled commitments and late events. Work due within 48 hours is prioritised by deadline; other work is prioritised by weighting. Study fills free gaps, up to 50 minutes per session with breaks, and respects the daily study-time cap.

## Main files

- `app.py`: registers four pages and shows a sidebar divider below Dashboard.
- `app_state.py`: shared plan storage and the adapter between frontend `fixed_events` and planner `fixedEvents`.
- `dashboard.py`: generated timeline, deadline cards and a link to My Timetable.
- `planner.py`: imported daily classes, arrows, weekly commitments, study availability, planning and export.
- `assignments.py` / `assignments_page.py`: demo/manual assignments and optional PDF review.
- `rescue.py`: reusable disruption component and before/after view, shown by `rescue_page.py`.
- `components.py`, `styles.py`, `helper_functions.py`: teammate's display approach with escaped text and Dublin-aware timestamps. No shadcn package is needed for these components.
- `calendar_import.py`, `timetable_store.py`, `timetable_ui.py`: recurring semester imports and saved calendar/day view.
- `assignment_bridge.py`: stable generated IDs, total hours converted to minutes, deadlines and weighting.
- `study_planner/`: friend's service, scheduler, interpreter, PDF extraction, validation and calendar export.

Assignment checklists are shown as supplied. The total hours schedule sessions for the whole assignment, rather than inventing an estimate for each checklist item. All required packages are in `requirements.txt`.

## Current scope

This is a daily planner, not a semester-wide allocation system. Plans on different dates do not share completion progress yet. Today uses actual time; other dates are previews beginning at the chosen study start. The dashboard/rescue page shows the last active generated plan and explicitly displays its date. Navigating to a day without a generated plan shows its classes; it does not generate study automatically.

Elapsed planned study is assumed completed unless reported missed or affected by a late event. Pressing **Plan my study time** rebuilds from assignment records. Changing assignments or adding a commitment invalidates generated plans, so generate them again.

The timetable is saved locally and reloads through its bookmarked URL. Hosting needs persistent disk; anyone with the link can access the saved timetable. Login is not implemented. Assignments, commitments and plans currently use session state and reset in a new session.

Imported class entries are preserved without overlap warnings. Study avoids their occupied time. There is no Brightspace connection; demo assignments and marks are fake. No real student calendar or API key is bundled.

## Git

This folder is a complete replacement integration example. Copy its files into the team repository and merge these packages with any existing `requirements.txt`; retain packages used by other team features. Keep `.env` and saved timetable data out of Git (the included `.gitignore` covers them). The older `navigation.py`, `sample_data.py` and testing `page2.py` are not needed by this app.

## Checks

```bash
python3 -m unittest discover -s tests -v
```

18 offline tests cover recurring calendar imports/storage, IDs, weighting, daily caps, all six disruptions, late-class progress, AI failure fallback, ICS export and the multi-page assignments → timetable → dashboard → rescue flow. Live OpenRouter calls have not been exercised.

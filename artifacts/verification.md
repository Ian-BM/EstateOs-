# Estate OS verification — 14 October 2026

- `python manage.py check`: passed, no issues.
- `python manage.py makemigrations`: no changes after committed initial migrations.
- `python manage.py migrate`: passed; all migrations applied to SQLite.
- `python manage.py test`: 23 tests passed.
- Chrome browser workflow run: 17 checks passed; no JavaScript page errors.
- Read-only smoke check of seeded record detail/edit pages: 24 HTTP 200 responses.
- Desktop viewport: 1440 × 1000. Mobile emulation: 390 × 844.
- Verified public enquiry → agency lead → stage update → viewing; manager property creation → publication → public detail; local offline draft → reload → manual synchronization; persisted favorites; mobile navigation; no page overflow on tested public and workspace pages.
- Browser test records were removed after verification; the local demo database retains its 25-property portfolio.
- The owned development server was stopped after QA. Start it with `python manage.py runserver`.

Screenshots are in this folder. `browser-results.json` records the browser checks. Core workflow tests are in `tests/test_workflows.py`; the optional repeatable browser script is `tests/browser_smoke.py`.

Not verified: PostgreSQL, production deployment, physical mobile devices, Safari/Firefox, real SMTP delivery. Offline draft storage and manual synchronization are verified; full offline startup and automatic synchronization are not implemented.

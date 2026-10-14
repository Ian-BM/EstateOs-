# ESTATE OS

A single Django application connecting a public Tanzanian property marketplace, a property management workspace and an agency CRM. Python, Django templates/forms/ORM, SQLite, custom CSS and vanilla JavaScript. No frontend server or Node build step.

## Start locally

Requires Python 3.12 or newer. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open **http://127.0.0.1:8000/**. The database in this workspace has already been migrated and seeded. In the current environment, `.venv` can use the existing Django and Pillow installation; the commands above also work as a clean installation.

The application uses `Africa/Dar_es_Salaam` and TZS. All sample agencies, listings, professionals and testimonials are labeled. Sample photos are illustrative, not evidence of real inventory or actual Tanzanian destinations.

## Local demo accounts

| Role | Username | Initial password |
| --- | --- | --- |
| Agency Administrator | `demo_admin` | `EstateDemo2026!` |
| Property Manager | `demo_manager` | `EstateDemo2026!` |
| Real Estate Agent | `demo_agent` | `EstateDemo2026!` |

All three belong to **Coastal Living**, so they share property, lead and viewing records. Sign in at `/accounts/login/`. Use `/demo/` for a product introduction. The seed also creates seven additional sample staff accounts; `demo_agent3` belongs to Kilimanjaro Estates and `demo_agent5` to Island & City, useful for checking isolation. Their initial password is the same.

`seed_demo` is idempotent and preserves existing records, edits and passwords. It creates 3 agencies, 10 staff, 25 properties (22 published initially), 10 landlords, 15 tenants, units, leases, inspections, maintenance, transactions, leads, viewings, tasks and contacts. It refuses to run with `DJANGO_DEBUG=0`. It never creates a platform superuser. If a demo username belongs to a different agency or role, it stops rather than overwriting it.

Create a separate platform administrator when needed:

```sh
python manage.py createsuperuser
```

Platform administration is `/admin/`. Agency administrators are ordinary application users, not Django staff. The platform administrator manages memberships and administratively reviewed verification flags in Django admin. New agency registrations create their own agency and an administrator membership. Existing agency staff accounts are provisioned by the platform administrator in this first version.

## Try the connected workflows

1. **Publish a property:** sign in as `demo_agent`, open Management → Properties → Add. Save the property as a private draft. Sign out using the sidebar button. Sign in as `demo_manager`, open the draft and select **Approve & publish**. It now appears in `/properties/`. Editing a published property as an agent returns it to draft; a manager must approve again.
2. **Enquiry to lead:** open a published property's public detail page and submit an enquiry. Checking “Request a viewing” records a request for the agency to arrange a date; it does not invent or confirm an appointment. In Coastal Living's CRM → Leads, open the new customer and update the stage. Both the manager and agent see the saved stage.
3. **Schedule a viewing:** from a lead detail page, select **Schedule viewing**, choose an agent, enter a date and save. Upcoming requested/confirmed viewings appear in the CRM overview.
4. **Property operations:** as manager, add units, register a tenant and create an active lease. The unit becomes occupied. Ending or archiving the active lease recalculates occupancy. Add an inspection or maintenance request; dashboard counts reflect current stored data.
5. **Manual finance:** record an external transaction. Managers can record pending transactions; only agency administrators can set verified/rejected status. Reports separate the verification states and transaction types. Estate OS never receives, holds, transfers or collects money.
6. **Export:** each record list has a scoped CSV export. Report pages link to the relevant source exports. Spreadsheet formula prefixes are escaped.

## Pages

Public: `/`, `/properties/`, `/properties/<slug>/`, `/agents/`, `/agents/<id>/`, `/agencies/`, `/agencies/<id>/`, `/pricing/`, `/about/`, `/contact/`, `/demo/`.

Accounts: `/accounts/register/`, `/accounts/login/`, POST `/accounts/logout/`, and Django's password reset routes under `/accounts/`. Password reset links print to the terminal with the default console email backend. Configure SMTP for real email.

Management: `/workspace/`, `/workspace/records/properties/`, `units`, `landlords`, `tenants`, `leases`, `inspections`, `maintenance`, `financial-records`, `documents`, plus `/workspace/reports/` and `/workspace/settings/`.

CRM: `/workspace/crm/`, `/workspace/records/leads/`, `/workspace/pipeline/`, `/workspace/agents/`, `/workspace/assignments/`, `/workspace/records/viewings/`, `tasks`, `contacts`, `/workspace/performance/`.

Every record collection supports create, detail, edit and archive routes. Archive actions are manager-only and use POST. Lists paginate and support text search; leads also filter by stage. The public directory supports rent/sale, region, free text, type, category, min/max price, bedrooms, availability, sorting and pagination.

## Project structure

```text
manage.py                 Django entry point
config/                   Settings, URLs, WSGI and ASGI
accounts/                 Registration and built-in authentication integration
agencies/                 Agencies and role memberships
properties/               Properties, listing publication and public enquiries/views
management/               Operations models and migrations
crm/                      Leads, viewings, tasks, contacts and migrations
core/                     Shared scoped forms, permissions, record registry,
                          workspace views, occupancy service and seed_demo
  management/commands/    Idempotent local demonstration seeding
templates/                Reusable public, account and workspace templates
static/css/               Central palette, public/dashboard and responsive styles
static/js/                Navigation, gallery, favorites and local draft prototype
static/images/            Locally stored illustrative photographs
media/                    Validated uploaded files (ignored by Git)
tests/                    Django workflow/permission tests and optional browser QA
artifacts/                Browser screenshots and verification results
```

## Database models

- `Agency`, `AgencyMembership` (one agency membership per user in this release).
- `Property`, `PropertyImage`, `PublicListing`, `Enquiry`.
- `PropertyUnit`, `Landlord`, `Tenant`, `Lease`, `Inspection`, `MaintenanceRequest`, `TransactionRecord`, `Document`.
- `Lead`, `Viewing`, `Task`, `Contact`.

Private records carry an agency foreign key. Record lookups and foreign-key choices are scoped on the server. Listing status and approval metadata are separate from private property details. Monetary fields use decimals. Database constraints enforce nonnegative amounts, lease date ordering, unique unit identifiers, one active unarchived lease per unit and unique offline operation IDs. Relevant foreign keys and public filter/stage fields are indexed.

## Permissions and uploads

- Agency administrators and property managers operate the portfolio and CRM. Agents manage draft properties, inspections and CRM records in their agency.
- Only managers/admins publish or archive. Only agency administrators verify financial records.
- Foreign agency IDs are rejected on reads, updates, publication, lead-stage changes, related-record fields and document downloads.
- Photo requests check public publication status or matching agency membership. Private documents and inspection photos require matching membership. There is **no public `/media/` catch-all**.
- Uploads are limited to 5 MB and accepted file extensions; image forms validate image content. Documents download as attachments. CSRF, Django password validation, sessions and template escaping stay enabled.
- Enquiries use a honeypot, validation and a 30-second per-session cooldown. A production-wide rate limit/CAPTCHA is not included.

## Offline draft prototype — exact limits

On **Create Inspection**, an authenticated user can save a local draft while the page is already open, including while the browser is offline. Browser `localStorage` holds only the property ID, date, inspection type, condition and a unique operation ID, partitioned by agency and user. It does not store photos, inspector identity, notes or customer information.

Drafts survive a reload and can be listed, loaded and deleted on that browser. Reconnect, reopen Create Inspection, load the draft, review/complete the fields and select **Save record**. The backend saves it once using its unique operation ID. Returning to the saved detail page marks the browser draft **Successfully synchronized**. Retrying the same operation returns the existing record instead of creating a duplicate.

This is **manual synchronization of a limited draft prototype**, not a full offline application. There is no service worker, cached-page startup, offline login, automatic background sync, offline photo upload or offline financial approval. Local storage is not encrypted and remains on the device until deleted. The page must first have loaded online. UUID support requires a modern browser and a secure context (localhost works).

## Configuration and future PostgreSQL deployment

`.env.example` documents the supported variables. No dotenv dependency is used: export variables in the process environment or configure them in your process manager. A `.env` file is not automatically read.

Local DEBUG defaults on. If no local secret is set, Django creates a random `.local-secret` with restrictive permissions; it is ignored by Git. For production, explicitly export `DJANGO_DEBUG=0`, a unique `DJANGO_SECRET_KEY` and your exact `DJANGO_ALLOWED_HOSTS`. Secure cookies, HTTPS redirect and HSTS are enabled outside DEBUG. Do not deploy demo credentials or a demo database.

For PostgreSQL, install `psycopg[binary]>=3.2` separately and set `DB_ENGINE=django.db.backends.postgresql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, then run migrations against a new database. The original local run verified SQLite. The production deployment separately verifies PostgreSQL; see `deploy/deployment-result.md`. A production deployment still needs a WSGI/ASGI server, HTTPS, static file serving, backups, SMTP, abuse controls and private file storage routing. Keep private media outside any unrestricted web-server alias. Run `python manage.py collectstatic` for the static assets. Production deployment instructions and the latest server result are in `deploy/README.md` and `deploy/deployment-result.md`.

## Verification

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
```

The core Django suite covers homepage/directory/details, actual filters, enquiries and CRM linking, login/POST logout, registration, complete password reset, dashboards/forms, agent draft creation, publication review, lead stage changes, viewing creation, tenants/leases and occupancy, maintenance/tasks, financial verification permissions, cross-agency access and forged foreign keys, CSRF, document/photo isolation, archival, idempotent inspection operations and repeatable demo seeding.

Optional browser QA uses **Playwright only as a development test tool**, not an application dependency. Install it separately (`python -m pip install playwright`) and run `.venv/bin/python tests/browser_smoke.py` with the local server and sample database available. It uses the installed macOS Chrome executable; change the test's executable path for another platform. The browser script creates clearly named QA records; use a disposable demo database for repeat runs. See `artifacts/browser-results.json` for the completed run and `artifacts/` for screenshots.

## Remaining first-version boundaries

- Offline draft capability is the prototype described above.
- Staff invitations, agency account switching, a granular per-agent “own records only” policy, audit history and team targets are future work. Current access boundaries are agency-wide with explicit role restrictions.
- Occupancy follows manually maintained active lease status, not a background scheduler. Managers must end expired leases. Rent prorating, accounting, arrears, reconciliation and payment processing are outside this release.
- Public enquiry email/SMS notifications are not implemented; enquiries are visible in the CRM. Contact details and commercial pricing remain clearly labeled placeholders.
- Gallery uploads are added one photo at a time through property editing. There is no photo ordering/removal UI; the platform administrator can manage images. Document versioning and malware scanning are not implemented.
- Verification flags are reviewed by a platform administrator in Django admin. Demo professionals and listings are not automatically verified. Testimonials are labeled illustrative samples.
- Property publication has a manager approval action; it is not a separate revision/version review system. Managers can directly edit approved listings.
- SQLite, modern desktop Chrome and mobile viewport emulation are the verification targets here; PostgreSQL, physical mobile devices and other browsers require their own validation.

Latest verification: **23 Django tests and 17 Chrome browser checks passed**, with no JavaScript page errors. System checks and migrations passed. Populated record detail/edit pages also passed a read-only HTTP smoke check. See [the verification report](artifacts/verification.md), [browser results](artifacts/browser-results.json), [desktop preview](artifacts/home-preview.png) and [mobile preview](artifacts/home-mobile-preview.png). The temporary server was stopped after QA.

The local generated sunset hero is [static/images/hero-v2.png](static/images/hero-v2.png). [Image credits](static/images/CREDITS.md) include its final prompt and built-in generation mode, plus the source IDs and license link for the other local photographs.


Editable agency demos: the production administrator can copy the original sample portfolio and linked operations/CRM into a registered agency using `python manage.py copy_demo_to_agency --agency-id <id> --expected-name "Exact agency name"`. This preserves existing records and logins, creates private draft sample listings, remaps every related record into that agency, and records an import manifest so repeated runs preserve edits without duplication. See [the deployment guide](deploy/README.md#editable-sample-data-for-a-registered-agency).


Mobile layouts: the responsive release was verified at 320–1440px, including public pages, management, CRM, records and forms. See [responsive QA](artifacts/responsive-verification.md) and [live results](artifacts/responsive-live-browser-results.json). The optional `tests/responsive_smoke.py` uses local sample credentials by default and accepts `ESTATE_QA_URL`, `ESTATE_QA_USERNAME` and `ESTATE_QA_PASSWORD` environment variables for a dedicated test environment. Never put production passwords in test source or Git.

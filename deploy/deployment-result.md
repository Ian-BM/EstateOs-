# Live deployment — 14 October 2026

- Public URL: **https://afyasoft.co.tz/**
- Server: `167.86.82.106` (Ubuntu 24.04, Python 3.12).
- Main-domain replacement explicitly approved by the owner; original AfyaSoft retained for rollback.
- Runtime source commit: `28c6786ebaadd8d03edf39ca0852c2981d02e211` (responsive layout update).
- Active release: `/srv/estate-os/releases/28c6786ebaadd8d03edf39ca0852c2981d02e211`.
- Application: `estate-os.service`, Gunicorn on `127.0.0.1:8010`, dedicated unprivileged `estateos` system user.
- Database: dedicated PostgreSQL 16 `estateos` database/role; local Unix socket peer authentication. The app role is neither superuser nor allowed to create databases.
- Persistent uploads: `/srv/estate-os/shared/media`; no public media alias.
- Root-only environment: `/etc/estate-os/production.env`; a fresh production secret was generated on the server and never copied into Git.
- TLS: existing valid Let's Encrypt certificate for the apex and www names, with active `certbot.timer`. Existing Cloudflare DNS/proxy routing was retained.
- HTTP and www redirect to the HTTPS apex domain.
- DEBUG off; secure cookies, HTTPS redirects and controlled forwarded-protocol handling enabled. Django deployment checks report only the deliberately omitted HSTS include-subdomains/preload options, to avoid applying a blanket policy to the shared domain's other subdomains.

## Verification

- 25 automated workflow/permission tests passed locally on SQLite.
- 25 tests passed on the VPS against a separate PostgreSQL `test_estateos` database, using HTTPS test requests and keeping production HTTPS protections enabled.
- Production schema migrations completed successfully.
- 25 labeled sample properties loaded. All 10 sample users are inactive and have unusable passwords. The public local demo password was rejected in a live Chrome login check.
- Eight live Chrome checks passed: homepage/photos, eleven public/account routes, database filters, private-workspace authentication redirect, login/CSRF behavior, secure HttpOnly CSRF cookie, four mobile layouts without page overflow, and mobile navigation.
- No JavaScript page errors were observed. Live checks created no agency/property/customer records.
- Public HTTPS returned 200; HTTP and www returned 301 to `https://afyasoft.co.tz/`.
- `estate-os`, `gunicorn-afyasoft`, nginx, certificate renewal and backup timers were active after deployment.
- The preserved original AfyaSoft application still returned its HTML through `/var/www/afyasoft/afyasoft.sock`.

Live screenshots: `artifacts/live-home-desktop.png` and `artifacts/live-home-mobile.png`. The browser check results are `artifacts/live-browser-results.json`.

## Backup and rollback

Original main-domain nginx configuration:

`/var/backups/estate-os/afyasoft-nginx-before-20261014T103807Z.conf`

Restore it without changing either application's data:

```sh
cp /var/backups/estate-os/afyasoft-nginx-before-20261014T103807Z.conf /etc/nginx/sites-available/afyasoft
nginx -t && systemctl reload nginx
```

Original service `gunicorn-afyasoft` and `/var/www/afyasoft` were not changed or stopped. Its database was not modified.

The first Estate OS backup completed at `/var/backups/estate-os/20261014T103808Z/`, containing the PostgreSQL dump, uploads archive, root-only environment copy and release reference. `estate-os-backup.timer` runs daily at 02:30 UTC / 05:30 Tanzania time plus up to ten minutes of jitter. These are local VPS backups; a separate off-server backup destination has not been configured.

## Access and remaining configuration

Use **Register your agency** to create a real business account. No default production administrator or working demo password is exposed. A platform superuser can be provisioned separately via the server CLI with a unique private password.

SMTP delivery remains unconfigured; password-reset messages currently go to the service log. The limited offline draft/manual-sync prototype and other functional boundaries in the README remain unchanged. Physical devices and non-Chrome browsers have not been tested in this deployment.


## Editable agency sample import — 14 October 2026

At the owner's explicit request, the original sample dataset was copied into the existing **DEMO REAL ESTATE** agency, preserving its existing administrator account and any existing records. An import manifest in `core.DemoDataImport` makes this a one-time, transactional copy; retries preserve user edits and do not duplicate records.

Imported: 25 properties, 44 units, 10 landlords, 15 tenants, 13 leases, 9 inspections, 9 maintenance requests, 9 manual financial samples, 18 leads, 10 viewings, 18 tasks and 18 contacts, plus 10 disabled sample staff profiles. Every relationship points to the new copies within that agency. Incoming public enquiries, actual customer records, documents and uploaded media were excluded.

Copied properties start as private drafts and retain a sample-content flag if the agency later publishes them. The workspace banner identifies the editable demonstration records. The original public sample listings remain available. No passwords or existing agency settings were changed.

Verification: 29 automated tests passed locally and on the server's separate PostgreSQL test database. Import tests cover related-record isolation, preservation of existing records, successful editing/publication, disabled sample logins, repeat imports and refusal of incorrect targets/incomplete source data. After the production import, every manifest count was checked and both populated dashboards rendered successfully using the existing administrator's permissions, without changing the administrator's login session.

Pre-update backup: `/var/backups/estate-os/20261014T111458Z/`. The new runtime schema additions are `core.0001_initial` and `properties.0002_property_is_sample`; the update did not change nginx or the retained AfyaSoft application.


## Responsive release — 14 October 2026

Deployed release `28c6786ebaadd8d03edf39ca0852c2981d02e211`. Phone layouts now use a naturally flowing hero/search form, readable text and touch controls, labeled record cards, scrollable report tables, a swipeable CRM pipeline, and an accessible drawer with backdrop/close/Escape/focus handling. CSS and JavaScript asset URLs include the release identifier to avoid reusing old cached styles.

Local Chrome verification checked 102 page/viewport combinations at 320, 375, 430, 768, 1024 and 1440 pixels. All 29 tests passed locally and again on the server's separate PostgreSQL test database. Eight live public Chrome checks passed after deployment, including four phone layouts and mobile navigation, without JavaScript page errors. The new versioned stylesheet returned HTTP 200. Estate OS, nginx and the preserved AfyaSoft service were active.

Pre-update backup: `/var/backups/estate-os/20261014T114032Z/`. No migrations were needed and no agency records or account passwords were changed by the responsive release. Current screenshots and browser results use the `responsive-live-` prefix under `artifacts/`. Physical phone hardware has not been tested.

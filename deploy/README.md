# Contabo deployment

Target: `167.86.82.106`, primary URL `https://afyasoft.co.tz/`.

Estate OS uses its own `/srv/estate-os` directory, `estateos` system user, PostgreSQL database/role, loopback port 8010 and `estate-os.service`. The previous AfyaSoft source, service, database and TLS certificate are preserved. Only the nginx configuration for the explicitly approved primary domain is replaced at cutover.

## Layout

- `/srv/estate-os/releases/<commit>/`: immutable application releases.
- `/srv/estate-os/current`: active release symlink.
- `/srv/estate-os/venv`: dedicated Python 3.12 environment.
- `/srv/estate-os/shared/media`: persistent private uploads, outside release trees.
- `/etc/estate-os/production.env`: root-only production environment and generated secret.
- PostgreSQL `estateos`: dedicated database and non-superuser role using local Unix-socket peer authentication.
- `/var/backups/estate-os/`: nginx rollback copy and daily private database/media/config backups.

Dependencies in `requirements-production.txt` add Gunicorn and psycopg to the existing Django/Pillow application. There is no frontend build. Nginx terminates TLS and serves collected static files; all private upload access goes through Django. Gunicorn trusts forwarded protocol headers only from loopback, and nginx overwrites them. DEBUG is off and secure cookies/HTTPS redirects are enabled. HSTS deliberately does not include all subdomains or preload the shared domain.

`prepare-server.py` creates an isolated service after receiving an extracted, reviewed release. It does **not** change nginx. `nginx-main.conf` is the explicit main-domain cutover configuration. The production environment is not stored in Git. Initial showcase seeding uses `seed_demo --showcase-only`: all sample logins are inactive and their passwords unusable. Use Register your agency for a real workspace; no default production administrator is created.

## Operations

```sh
systemctl status estate-os
journalctl -u estate-os -n 100 --no-pager
systemctl restart estate-os
systemctl status estate-os-backup.timer
/usr/local/sbin/estate-os-backup
```

Backups run daily at 02:30 UTC (05:30 Tanzania time), plus up to ten minutes of jitter. They are root-readable snapshots on this VPS; copy them to separate storage for disaster recovery. Backups are retained until the administrator removes them; monitor disk use.

For updates, create and test a new commit, extract it into a new release directory, install dependencies, back up the current database, run migrations and collectstatic, then switch `current` and restart `estate-os`. Run PostgreSQL tests against an isolated pre-created test database. Do not reuse another application's database or grant the production role CREATEDB/superuser privileges.

## Rollback

The actual nginx backup path and deployed commit are recorded in `deployment-result.md` after cutover. To restore the former AfyaSoft site, copy that nginx backup over `/etc/nginx/sites-available/afyasoft`, run `nginx -t`, then `systemctl reload nginx`. Its original `gunicorn-afyasoft` service remains running; its files and database are untouched by Estate OS.

An Estate OS application rollback changes `current` to a previous release and restarts `estate-os`. Database migrations may require a matching database restore; never assume a source rollback reverses schema changes.

SMTP credentials are not configured by this deployment. Password-reset emails use the console backend until SMTP is supplied. The application's existing offline draft feature remains a limited manual-sync prototype.

## Editable sample data for a registered agency

An administrator can copy the original synthetic dataset into a real agency workspace:

```sh
python manage.py copy_demo_to_agency --agency-id 4 --expected-name "DEMO REAL ESTATE"
```

Run with the application's production environment and system user. The exact name check prevents an accidental import into another agency. The import is transactional and runs once per agency; its `DemoDataImport` manifest preserves the source-to-copy mapping. Re-running preserves existing records and user edits. It adds 25 sample properties, the linked operations/CRM records and disabled sample staff, with every relationship reassigned to the destination agency. Existing real records and the owner's account stay intact. It copies only known synthetic seed records, excluding public enquiries, actual visitors, documents and uploaded media. Copied listings start as private drafts, carry a persistent sample-content label and require the agency's normal publication action. Imported financial records are explicitly illustrative. A workspace banner identifies the imported dataset.

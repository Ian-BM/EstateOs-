"""Run as root via SSH after extracting a reviewed source release.
Starts Estate OS on loopback only; does not change nginx or another application.
"""
import grp,os,pwd,secrets,subprocess,sys
from pathlib import Path

def run(args,**kwargs):
    return subprocess.run(args,check=True,**kwargs)

release=Path(sys.argv[1]).resolve()
if release.parent!=Path('/srv/estate-os/releases') or not (release/'manage.py').is_file():
    raise SystemExit('Expected an extracted Estate OS release under /srv/estate-os/releases.')
base=Path('/srv/estate-os')
try: app_user=pwd.getpwnam('estateos')
except KeyError:
    run(['useradd','--system','--user-group','--home-dir',str(base),'--shell','/usr/sbin/nologin','estateos'])
    app_user=pwd.getpwnam('estateos')
shared=base/'shared';shared.mkdir(mode=0o750,exist_ok=True)
(shared/'media').mkdir(mode=0o750,exist_ok=True)
for path in [shared,shared/'media']: os.chown(path,app_user.pw_uid,app_user.pw_gid)
config=Path('/etc/estate-os');config.mkdir(mode=0o700,exist_ok=True)
env_path=config/'production.env'
if not env_path.exists():
    environment={
        'DJANGO_DEBUG':'0','DJANGO_SECRET_KEY':secrets.token_urlsafe(64),
        'DJANGO_ALLOWED_HOSTS':'afyasoft.co.tz,www.afyasoft.co.tz,estate.afyasoft.co.tz,127.0.0.1,localhost',
        'DJANGO_CSRF_TRUSTED_ORIGINS':'https://afyasoft.co.tz,https://www.afyasoft.co.tz,https://estate.afyasoft.co.tz',
        'DJANGO_TRUST_PROXY':'1','DJANGO_MEDIA_ROOT':str(shared/'media'),
        'DB_ENGINE':'django.db.backends.postgresql','DB_NAME':'estateos','DB_USER':'estateos',
        'DB_HOST':'/var/run/postgresql','DB_PORT':'5432',
        'DEFAULT_FROM_EMAIL':'Estate OS <noreply@afyasoft.co.tz>',
    }
    env_path.write_text(''.join(f'{key}={value}\n' for key,value in environment.items()))
    env_path.chmod(0o600)
env={**os.environ,**dict(line.split('=',1) for line in env_path.read_text().splitlines() if line and not line.startswith('#'))}
role=subprocess.check_output(['runuser','-u','postgres','--','psql','-Atc',"SELECT rolname FROM pg_roles WHERE rolname='estateos'"],text=True).strip()
if not role: run(['runuser','-u','postgres','--','createuser','--no-superuser','--no-createdb','--no-createrole','estateos'])
database=subprocess.check_output(['runuser','-u','postgres','--','psql','-Atc',"SELECT datname FROM pg_database WHERE datname='estateos'"],text=True).strip()
if not database: run(['runuser','-u','postgres','--','createdb','--owner=estateos','estateos'])
venv=base/'venv'
if not (venv/'bin/python').exists(): run(['python3','-m','venv',str(venv)])
run([str(venv/'bin/python'),'-m','pip','install','--disable-pip-version-check','-r',str(release/'requirements-production.txt')])
# root installs immutable source; service reads it but cannot modify the release.
run(['chmod','-R','a+rX',str(release)])
static=release/'staticfiles';static.mkdir(exist_ok=True);os.chown(static,app_user.pw_uid,app_user.pw_gid)
def manage(*args):
    run(['runuser','-u','estateos','--',str(venv/'bin/python'),str(release/'manage.py'),*args],cwd=release,env=env)
manage('check','--deploy')
manage('migrate','--noinput')
# Empty production database gets illustrative inventory with no usable sample logins.
seed_marker=shared/'.showcase-seeded'
if not seed_marker.exists():
    manage('seed_demo','--showcase-only')
    seed_marker.touch(mode=0o600)
manage('collectstatic','--noinput')
# Static files are read-only to the running application.
run(['chown','-R','root:root',str(static)])
current=base/'current'
next_link=base/'current.next'
if next_link.is_symlink(): next_link.unlink()
next_link.symlink_to(release)
next_link.replace(current)
run(['install','-m','644',str(release/'deploy/estate-os.service'),'/etc/systemd/system/estate-os.service'])
run(['systemctl','daemon-reload'])
run(['systemctl','enable','estate-os.service'])
run(['systemctl','restart','estate-os.service'])
print('Estate OS prepared on 127.0.0.1:8010. Existing nginx routing has NOT been changed.')

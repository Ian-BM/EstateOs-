"""Explicitly approved main-domain cutover, with nginx backup and automatic rollback."""
import datetime,shutil,subprocess,urllib.request
from pathlib import Path

def run(args,**kwargs): return subprocess.run(args,check=True,**kwargs)
base=Path('/srv/estate-os');release=(base/'current').resolve()
request=urllib.request.Request('http://127.0.0.1:8010/',headers={'Host':'afyasoft.co.tz','X-Forwarded-Proto':'https'})
with urllib.request.urlopen(request,timeout=20) as response:
    assert response.status==200 and b'ESTATE OS' in response.read()
run(['systemctl','is-active','gunicorn-afyasoft.service'])
backup_root=Path('/var/backups/estate-os');backup_root.mkdir(mode=0o700,exist_ok=True)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
old=Path('/etc/nginx/sites-available/afyasoft')
backup=backup_root/f'afyasoft-nginx-before-{stamp}.conf'
shutil.copy2(old,backup)
backup.chmod(0o600)
try:
    shutil.copyfile(release/'deploy/nginx-main.conf',old)
    run(['nginx','-t'])
    run(['systemctl','reload','nginx'])
    result=subprocess.check_output(['curl','--fail','--silent','--show-error','--max-time','25','--resolve','afyasoft.co.tz:443:127.0.0.1','https://afyasoft.co.tz/'])
    assert b'ESTATE OS' in result and b'Find Your Next Property.' in result
except Exception:
    shutil.copyfile(backup,old)
    run(['nginx','-t'])
    run(['systemctl','reload','nginx'])
    print('Cutover failed; original AfyaSoft nginx configuration restored.')
    raise
run(['install','-m','700',str(release/'deploy/backup.sh'),'/usr/local/sbin/estate-os-backup'])
for name in ['estate-os-backup.service','estate-os-backup.timer']:
    run(['install','-m','644',str(release/'deploy'/name),'/etc/systemd/system/'+name])
run(['systemctl','daemon-reload'])
run(['systemctl','enable','--now','estate-os-backup.timer'])
run(['/usr/local/sbin/estate-os-backup'])
run(['systemctl','is-active','estate-os.service','gunicorn-afyasoft.service','nginx.service'])
print('LIVE_URL=https://afyasoft.co.tz/')
print('PREVIOUS_NGINX_BACKUP='+str(backup))
print('ACTIVE_RELEASE='+str(release))
print('The original AfyaSoft service, files and database remain unchanged.')

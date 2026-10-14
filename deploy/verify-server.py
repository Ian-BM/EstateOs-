"""Verify an isolated production instance and run tests on a separate PostgreSQL DB."""
import os,subprocess
from pathlib import Path
base=Path('/srv/estate-os');release=(base/'current').resolve()
env={**os.environ,**dict(line.split('=',1) for line in Path('/etc/estate-os/production.env').read_text().splitlines() if line and not line.startswith('#'))}
exists=subprocess.check_output(['runuser','-u','postgres','--','psql','-Atc',"SELECT datname FROM pg_database WHERE datname='test_estateos'"],text=True).strip()
if not exists: subprocess.run(['runuser','-u','postgres','--','createdb','--owner=estateos','test_estateos'],check=True)
env['DJANGO_SETTINGS_MODULE']='config.settings'
# Exercise workflow tests over HTTPS, matching the production proxy rather than
# disabling the application's SSL redirects for an HTTP-only test client.
bootstrap="""
import django
django.setup()
from django.test import Client
from django.core.management import call_command
original_request=Client.request
def https_request(self,**request):
    request['wsgi.url_scheme']='https'
    request['SERVER_PORT']='443'
    return original_request(self,**request)
Client.request=https_request
call_command('test',keepdb=True,interactive=False)
"""
subprocess.run(['runuser','-u','estateos','--',str(base/'venv/bin/python'),'-c',bootstrap],cwd=release,env=env,check=True)
# Assert that the production DB remains populated only with disabled sample users.
code="from django.contrib.auth.models import User; from properties.models import Property; assert Property.objects.count()==25; assert not User.objects.filter(is_active=True).exists(); assert all(not u.has_usable_password() for u in User.objects.all()); print('Production showcase: 25 properties; all sample logins disabled.')"
subprocess.run(['runuser','-u','estateos','--',str(base/'venv/bin/python'),str(release/'manage.py'),'shell','-c',code],cwd=release,env=env,check=True)

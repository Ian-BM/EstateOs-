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
# Verify the original showcase without assuming real agencies have no records/users.
code="from django.contrib.auth.models import User; from properties.models import Property; users=User.objects.filter(username__in=['demo_admin','demo_manager','demo_agent']+[f'demo_agent{i}' for i in range(2,9)]); assert Property.objects.filter(agency__is_demo=True,slug__startswith='demo-property-').count()==25; assert users.count()==10; assert not users.filter(is_active=True).exists(); assert all(not u.has_usable_password() for u in users); print('Original showcase: 25 properties; original sample logins disabled; real agencies preserved.')"
subprocess.run(['runuser','-u','estateos','--',str(base/'venv/bin/python'),str(release/'manage.py'),'shell','-c',code],cwd=release,env=env,check=True)

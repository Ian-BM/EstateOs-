"""Run via SSH as root with --agency-id / --expected-name; retains existing logins/data."""
import argparse,os,subprocess
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--agency-id',type=int,required=True)
parser.add_argument('--expected-name',required=True)
args=parser.parse_args()
release=Path('/srv/estate-os/current').resolve()
env={**os.environ,**dict(line.split('=',1) for line in Path('/etc/estate-os/production.env').read_text().splitlines() if line and not line.startswith('#'))}
command=['runuser','-u','estateos','--','/srv/estate-os/venv/bin/python',str(release/'manage.py')]
subprocess.run(command+['copy_demo_to_agency','--agency-id',str(args.agency_id),'--expected-name',args.expected_name],cwd=release,env=env,check=True)
verification=f"""
from django.test import RequestFactory
from agencies.models import Agency
from core.models import DemoDataImport
from core.views import dashboard
from core.registry import RECORDS
from properties.models import Property,PublicListing
agency=Agency.objects.get(pk={args.agency_id!r},name={args.expected_name!r})
record=DemoDataImport.objects.get(agency=agency)
for label,ids in record.manifest.items():
    from django.apps import apps
    model=apps.get_model(label)
    assert model.objects.filter(pk__in=ids.values(),agency=agency).count()==len(ids)
print('COPIED_COUNTS',{{label:len(ids) for label,ids in record.manifest.items()}})
props=Property.objects.filter(agency=agency,is_sample=True)
assert props.count()==25
assert not PublicListing.objects.filter(property__in=props).exclude(status='draft').exists()
owner=agency.memberships.filter(role='admin',user__is_active=True).select_related('user').first()
assert owner,'The existing real agency administrator must remain active.'
for section in ['management','crm']:
    request=RequestFactory().get('/workspace/',secure=True,HTTP_HOST='afyasoft.co.tz')
    request.user=owner.user
    response=dashboard(request,section=section)
    assert response.status_code==200
    assert b'SAMPLE DATA LOADED' in response.content
print('Existing administrator can open both populated dashboards. All imported listings are private drafts.')
"""
subprocess.run(command+['shell','-c',verification],cwd=release,env=env,check=True)

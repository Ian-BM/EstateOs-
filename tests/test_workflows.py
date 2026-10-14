import io,uuid
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase,Client,override_settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from agencies.models import Agency,AgencyMembership
from properties.models import Property,PublicListing,Enquiry,PropertyImage
from management.models import PropertyUnit,Tenant,Lease,MaintenanceRequest,Inspection,TransactionRecord,Document
from crm.models import Lead,Viewing,Task
from core.forms import scoped_form
from core.registry import RECORDS

class Workflows(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a=Agency.objects.create(name='Alpha',city='Dar es Salaam')
        cls.b=Agency.objects.create(name='Beta',city='Arusha')
        cls.members={}
        for username,role,agency in [('admin','admin',cls.a),('manager','manager',cls.a),('agent','agent',cls.a),('other','admin',cls.b)]:
            user=User.objects.create_user(username,password='StrongPass2026!',email=username+'@example.com')
            cls.members[username]=AgencyMembership.objects.create(user=user,agency=agency,role=role)
        cls.prop=cls.make_property(cls.a,'ocean-house',assigned_agent=cls.members['agent'])
        cls.foreign=cls.make_property(cls.b,'foreign-house',region='Arusha',purpose='sale',price=500000000)
        PublicListing.objects.create(property=cls.prop,status='published',published_at=timezone.now(),featured=True)
        PublicListing.objects.create(property=cls.foreign,status='draft')
        cls.lead=Lead.objects.create(agency=cls.a,name='Alice',phone='+255712345678',property=cls.prop,assigned_agent=cls.members['agent'])
        cls.foreign_lead=Lead.objects.create(agency=cls.b,name='Private Beta Lead',phone='+255712345678',property=cls.foreign)
        cls.unit=PropertyUnit.objects.create(agency=cls.a,property=cls.prop,identifier='A1',unit_type='Apartment',size=80,rental_amount=500000)
        cls.foreign_unit=PropertyUnit.objects.create(agency=cls.b,property=cls.foreign,identifier='B1',unit_type='Apartment',size=80,rental_amount=500000)
        cls.tenant=Tenant.objects.create(agency=cls.a,name='Tenant One',phone='+255712345678')
    @staticmethod
    def make_property(agency,slug,**kwargs):
        data=dict(agency=agency,slug=slug,name=slug.title(),description='Sample space',property_type='house',purpose='rent',location='Masaki',region='Dar es Salaam',price=1000000,size=180,bedrooms=3,bathrooms=2)
        data.update(kwargs);return Property.objects.create(**data)
    def login(self,role='manager'):self.client.force_login(self.members[role].user)
    def form_payload(self,model,obj):
        form=scoped_form(model,self.members['manager'],instance=obj)
        data={}
        for name,field in form.fields.items():
            val=form[name].value()
            if val is not None: data[name]=val
        return data
    def test_public_pages_and_filters(self):
        for url in ['/','/properties/',self.prop.get_absolute_url(),'/agents/','/agencies/','/pricing/','/about/','/contact/','/demo/',f'/agents/{self.members["agent"].pk}/',f'/agencies/{self.a.pk}/']:
            with self.subTest(url=url):self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.get(self.foreign.get_absolute_url()).status_code,404)
        filters=[({'region':'Dar es Salaam','purpose':'rent','property_type':'house','min_price':900000,'max_price':1000000,'bedrooms':3,'availability':'available'},1),({'region':'Arusha'},0),({'category':'commercial'},0),({'min_price':2000000},0),({'max_price':'NaN'},0),({'min_price':'1e9999'},0),({'bedrooms':'999999999999'},0)]
        for query,count in filters:self.assertEqual(self.client.get('/properties/',query).context['page_obj'].paginator.count,count)
    def test_enquiry_links_correct_agency_and_lead(self):
        r=self.client.post(self.prop.get_absolute_url(),{'name':'Public Buyer','phone':'+255712345678','email':'a@example.com','message':'Please arrange a viewing','request_viewing':'on'})
        self.assertEqual(r.status_code,302)
        enquiry=Enquiry.objects.get();self.assertEqual(enquiry.agency,self.a);self.assertEqual(enquiry.listing,self.prop.listing)
        self.assertEqual(enquiry.lead.agency,self.a);self.assertEqual(enquiry.lead.assigned_agent,self.members['agent'])
        self.assertIn('Viewing requested',enquiry.lead.notes)
        self.login('agent');self.assertContains(self.client.get('/workspace/records/leads/'),'Public Buyer')
        self.login('other');self.assertNotContains(self.client.get('/workspace/records/leads/'),'Public Buyer')
    def test_spam_and_invalid_enquiries_rejected(self):
        payload={'name':'Bot','phone':'bad','message':'Hi','website':'spam.example'}
        self.assertEqual(self.client.post(self.prop.get_absolute_url(),payload).status_code,200);self.assertFalse(Enquiry.objects.exists())
        payload.update(phone='+255712345678',website='')
        self.client.post(self.prop.get_absolute_url(),payload);self.client.post(self.prop.get_absolute_url(),payload)
        self.assertEqual(Enquiry.objects.count(),1)
    def test_login_logout_and_private_redirect(self):
        self.assertEqual(self.client.get('/workspace/').status_code,302)
        r=self.client.post('/accounts/login/',{'username':'agent','password':'StrongPass2026!'})
        self.assertEqual(r.status_code,302);self.assertEqual(self.client.get('/workspace/').status_code,200)
        self.assertEqual(self.client.get('/accounts/logout/').status_code,405)
        self.assertEqual(self.client.post('/accounts/logout/').status_code,302);self.assertEqual(self.client.get('/workspace/').status_code,302)
    def test_registration_creates_admin_and_agency(self):
        r=self.client.post('/accounts/register/',{'username':'newowner','email':'new@example.com','agency_name':'New Agency','city':'Dodoma','password1':'A-unique-password-882','password2':'A-unique-password-882'})
        self.assertEqual(r.status_code,302);m=AgencyMembership.objects.get(user__username='newowner');self.assertEqual(m.role,'admin');self.assertEqual(m.agency.name,'New Agency')
    def test_password_reset_workflow(self):
        from django.core import mail
        r=self.client.post('/accounts/password_reset/',{'email':'agent@example.com'})
        self.assertEqual(r.status_code,302);self.assertEqual(len(mail.outbox),1)
        import re
        link=re.search(r'http[^\s]+',mail.outbox[0].body).group(0)
        path=link.split('testserver')[-1]
        r=self.client.get(path,follow=True);self.assertEqual(r.status_code,200)
        reset_path=r.redirect_chain[-1][0]
        self.client.post(reset_path,{'new_password1':'New-Unique-Password-982!','new_password2':'New-Unique-Password-982!'})
        self.assertTrue(self.client.login(username='agent',password='New-Unique-Password-982!'))
    def test_all_management_and_crm_pages(self):
        self.login()
        for url in ['/workspace/','/workspace/crm/','/workspace/pipeline/','/workspace/agents/','/workspace/assignments/','/workspace/performance/','/workspace/reports/','/workspace/settings/']:
            with self.subTest(url=url):self.assertEqual(self.client.get(url).status_code,200)
        for key,(model,_,_) in RECORDS.items():
            for suffix in ['', 'new/']:
                with self.subTest(key=key,suffix=suffix):self.assertEqual(self.client.get(f'/workspace/records/{key}/{suffix}').status_code,200)
    def test_agent_creates_draft_manager_publishes(self):
        self.login('agent');data=self.form_payload(Property,self.prop);data['name']='New agent property'
        r=self.client.post('/workspace/records/properties/new/',data)
        self.assertEqual(r.status_code,302,r.context and r.context['form'].errors)
        prop=Property.objects.get(name='New agent property');self.assertEqual(prop.listing.status,'draft');self.assertEqual(prop.agency,self.a)
        url=reverse('publish',args=[prop.pk]);self.assertEqual(self.client.post(url).status_code,403)
        self.login();self.assertEqual(self.client.get(url).status_code,405);self.assertEqual(self.client.post(url).status_code,302)
        prop.refresh_from_db();self.assertEqual(prop.listing.status,'published');self.assertEqual(self.client.get(prop.get_absolute_url()).status_code,200)
        self.login('agent');data['description']='Agent revision'
        self.client.post(reverse('record_edit',args=['properties',prop.pk]),data)
        prop.listing.refresh_from_db();self.assertEqual(prop.listing.status,'draft');self.assertEqual(self.client.get(prop.get_absolute_url()).status_code,404)
    def test_lead_stage_and_viewing_persist(self):
        self.login('agent');self.client.post(reverse('lead_stage',args=[self.lead.pk]),{'status':'qualified'})
        self.lead.refresh_from_db();self.assertEqual(self.lead.status,'qualified')
        r=self.client.post('/workspace/records/viewings/new/',{'property':self.prop.pk,'lead':self.lead.pk,'agent':self.members['agent'].pk,'date':(timezone.now()+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),'status':'confirmed','notes':'Bring keys'})
        self.assertEqual(r.status_code,302,r.context and r.context['form'].errors);self.assertEqual(Viewing.objects.get().agency,self.a)
        self.login();self.assertContains(self.client.get('/workspace/crm/'),'Alice')
    def test_tenant_lease_occupancy_and_archive(self):
        self.login()
        r=self.client.post('/workspace/records/tenants/new/',{'name':'New Tenant','phone':'0712345678','active':'on'})
        self.assertEqual(r.status_code,302)
        tenant=Tenant.objects.get(name='New Tenant')
        payload={'unit':self.unit.pk,'tenant':tenant.pk,'start_date':'2026-10-01','end_date':'2027-09-30','monthly_rent':500000,'status':'active'}
        r=self.client.post('/workspace/records/leases/new/',payload)
        self.assertEqual(r.status_code,302,r.context and r.context['form'].errors)
        self.unit.refresh_from_db();self.assertEqual(self.unit.occupancy,'occupied')
        self.assertEqual(self.client.get('/workspace/').context['stats'][2][1],1)
        self.assertEqual(self.client.post('/workspace/records/leases/new/',payload).status_code,200)
        lease=Lease.objects.get();self.client.post(reverse('archive',args=['leases',lease.pk]))
        self.unit.refresh_from_db();self.assertEqual(self.unit.occupancy,'vacant')
    def test_invalid_lease_dates(self):
        self.login();r=self.client.post('/workspace/records/leases/new/',{'unit':self.unit.pk,'tenant':self.tenant.pk,'start_date':'2027-01-01','end_date':'2026-01-01','monthly_rent':5,'status':'active'})
        self.assertEqual(r.status_code,200);self.assertFalse(Lease.objects.exists())
    def test_maintenance_and_task_creation(self):
        self.login();r=self.client.post('/workspace/records/maintenance/new/',{'property':self.prop.pk,'unit':self.unit.pk,'description':'Repair tap','priority':'urgent','assigned_person':self.members['manager'].pk,'status':'open'})
        self.assertEqual(r.status_code,302);self.assertEqual(MaintenanceRequest.objects.get().agency,self.a)
        r=self.client.post('/workspace/records/tasks/new/',{'title':'Call Alice','assigned_to':self.members['agent'].pk,'deadline':'2026-11-01T14:00','priority':'normal','lead':self.lead.pk,'property':self.prop.pk})
        self.assertEqual(r.status_code,302);self.assertFalse(Task.objects.get().completed)
        task=Task.objects.get();payload=self.form_payload(Task,task);payload['completed']='on';self.client.post(reverse('record_edit',args=['tasks',task.pk]),payload);task.refresh_from_db();self.assertTrue(task.completed)
    def test_agency_isolation_read_write_status_and_relations(self):
        self.login()
        for key,obj in [('properties',self.foreign),('leads',self.foreign_lead),('units',self.foreign_unit)]:
            for action in ['record_detail','record_edit','archive']:
                url=reverse(action,args=[key,obj.pk]);r=self.client.post(url,{}) if action=='archive' else self.client.get(url)
                self.assertEqual(r.status_code,404)
        self.assertEqual(self.client.post(reverse('publish',args=[self.foreign.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('lead_stage',args=[self.foreign_lead.pk]),{'status':'converted'}).status_code,404)
        data=self.form_payload(Property,self.prop);data['assigned_agent']=self.members['other'].pk
        r=self.client.post('/workspace/records/properties/new/',data);self.assertEqual(r.status_code,200);self.assertIn('assigned_agent',r.context['form'].errors)
        r=self.client.post('/workspace/records/maintenance/new/',{'property':self.prop.pk,'unit':self.foreign_unit.pk,'description':'Bad','priority':'normal','status':'open'})
        self.assertEqual(r.status_code,200);self.assertFalse(MaintenanceRequest.objects.exists())
    def test_agent_cannot_use_manager_operations(self):
        self.login('agent')
        for key in ['units','landlords','tenants','leases','maintenance','financial-records','documents']:
            self.assertEqual(self.client.get(f'/workspace/records/{key}/').status_code,403)
            self.assertEqual(self.client.post(f'/workspace/records/{key}/new/',{}).status_code,403)
        self.assertEqual(self.client.post(reverse('archive',args=['properties',self.prop.pk])).status_code,403)
        self.assertEqual(self.client.get('/workspace/settings/').status_code,403)
    def test_csrf_enforced(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.post(self.prop.get_absolute_url(),{'name':'Bad'}).status_code,403)
        c.force_login(self.members['manager'].user)
        self.assertEqual(c.post(reverse('publish',args=[self.prop.pk])).status_code,403)
    def test_financial_verification_requires_admin(self):
        self.login();payload={'property':self.prop.pk,'transaction_type':'rent','amount':'500000','payment_date':'2026-10-14','payment_method':'Bank','verification_status':'verified'}
        self.client.post('/workspace/records/financial-records/new/',payload)
        record=TransactionRecord.objects.get();self.assertEqual(record.verification_status,'pending')
        self.login('admin');self.client.post(reverse('record_edit',args=['financial-records',record.pk]),payload)
        record.refresh_from_db();self.assertEqual(record.verification_status,'verified')
        self.assertContains(self.client.get('/workspace/reports/'),'verified')
    def test_inspection_operations_are_idempotent(self):
        self.login('agent');op=str(uuid.uuid4());payload={'property':self.prop.pk,'date':'2026-11-01T12:00','inspection_type':'Routine','condition':'good','status':'pending','operation_id':op}
        self.assertEqual(self.client.post('/workspace/records/inspections/new/',payload).status_code,302)
        self.assertEqual(self.client.post('/workspace/records/inspections/new/',payload).status_code,302)
        self.assertEqual(Inspection.objects.filter(operation_id=op).count(),1)
    def test_export_is_scoped_and_csv_injection_safe(self):
        self.login();Lead.objects.create(agency=self.a,name='=HYPERLINK("bad")',phone='123456789')
        response=self.client.get('/workspace/records/leads/?export=csv')
        self.assertEqual(response.status_code,200);text=response.content.decode();self.assertNotIn('Private Beta Lead',text);self.assertIn("'=HYPERLINK",text)
    @override_settings(MEDIA_ROOT='/tmp/estate-os-test-media')
    def test_property_photos_and_private_documents(self):
        from PIL import Image
        image=io.BytesIO();Image.new('RGB',(10,10),'green').save(image,'PNG')
        photo=PropertyImage.objects.create(property=self.foreign,image=SimpleUploadedFile('private.png',image.getvalue(),content_type='image/png'))
        url=reverse('property_image',args=[photo.pk]);self.assertEqual(self.client.get(url).status_code,404)
        self.login();self.assertEqual(self.client.get(url).status_code,404)
        self.login('other');self.assertEqual(self.client.get(url).status_code,200)
        doc=Document.objects.create(agency=self.b,property=self.foreign,title='Private lease',file=SimpleUploadedFile('lease.pdf',b'%PDF-1.4 test'))
        self.login();self.assertEqual(self.client.get(reverse('document_download',args=[doc.pk])).status_code,404)
        self.assertEqual(self.client.get('/media/'+doc.file.name).status_code,404)
    def test_missing_membership_is_denied(self):
        u=User.objects.create_user('outsider',password='abc');self.client.force_login(u);self.assertEqual(self.client.get('/workspace/').status_code,403)
    def test_archived_properties_leave_public_directory(self):
        self.login();self.client.post(reverse('archive',args=['properties',self.prop.pk]));self.assertEqual(self.client.get(self.prop.get_absolute_url()).status_code,404)

class SeedTests(TestCase):
    @override_settings(DEBUG=True)
    def test_demo_command_is_idempotent(self):
        call_command('seed_demo',stdout=io.StringIO());counts=[m.objects.count() for m in [Agency,AgencyMembership,Property,PropertyUnit,Tenant,Lease,Lead,Viewing,TransactionRecord]]
        call_command('seed_demo',stdout=io.StringIO());self.assertEqual(counts,[m.objects.count() for m in [Agency,AgencyMembership,Property,PropertyUnit,Tenant,Lease,Lead,Viewing,TransactionRecord]])
        self.assertEqual(Agency.objects.count(),3);self.assertEqual(Property.objects.count(),25);self.assertEqual(AgencyMembership.objects.count(),10);self.assertEqual(Tenant.objects.count(),15)
    @override_settings(DEBUG=False)
    def test_demo_command_refuses_production(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):call_command('seed_demo',stdout=io.StringIO())

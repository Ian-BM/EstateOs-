import io
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth.models import User
from django.apps import apps
from agencies.models import Agency,AgencyMembership
from core.models import DemoDataImport
from properties.models import Property,PublicListing,Enquiry
from management.models import Tenant,Lease,PropertyUnit
from crm.models import Lead

class AgencyDemoImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo',showcase_only=True,stdout=io.StringIO())
        cls.target=Agency.objects.create(name='My Agency',city='Dar es Salaam')
        cls.owner=User.objects.create_user('real-owner',password='PersonalPass2026!')
        AgencyMembership.objects.create(user=cls.owner,agency=cls.target,role='admin')
        cls.property=Property.objects.create(agency=cls.target,name='My real property',slug='my-real-property',description='Real description',property_type='house',purpose='rent',location='Masaki',region='Dar es Salaam',price=1500000,size=120)
        PublicListing.objects.create(property=cls.property,status='published')
        Tenant.objects.create(agency=cls.target,name='Real Tenant',phone='0712345678')
        # Incoming public enquiries in a source agency must never be copied.
        source=Property.objects.get(slug='demo-property-01')
        lead=Lead.objects.create(agency=source.agency,name='Private visitor',phone='0712345678',source='Public directory',property=source)
        Enquiry.objects.create(agency=source.agency,listing=source.listing,name=lead.name,phone=lead.phone,message='Private enquiry',lead=lead)

    def copy(self,**kwargs):
        call_command('copy_demo_to_agency',agency_id=self.target.pk,expected_name='My Agency',stdout=io.StringIO(),**kwargs)

    def test_complete_editable_import_preserves_real_records_and_relations(self):
        self.copy()
        self.assertEqual(Property.objects.filter(agency=self.target,is_sample=True).count(),25)
        self.assertEqual(PropertyUnit.objects.filter(agency=self.target).count(),44)
        self.assertEqual(Tenant.objects.filter(agency=self.target).count(),16)
        self.assertEqual(Lease.objects.filter(agency=self.target).count(),13)
        self.assertEqual(Lead.objects.filter(agency=self.target).count(),18)
        self.assertFalse(Lead.objects.filter(agency=self.target,name='Private visitor').exists())
        self.assertFalse(Enquiry.objects.filter(agency=self.target).exists())
        self.assertEqual(Property.objects.get(pk=self.property.pk).description,'Real description')
        self.assertTrue(self.property.listing.status=='published')
        self.target.refresh_from_db();self.assertFalse(self.target.is_demo)
        for app in ['properties','management','crm']:
            for model in apps.get_app_config(app).get_models():
                if not any(f.name=='agency' for f in model._meta.fields): continue
                for obj in model.objects.filter(agency=self.target):
                    for field in model._meta.fields:
                        if field.is_relation and field.name!='agency':
                            value=getattr(obj,field.name)
                            if value is not None and hasattr(value,'agency_id'):
                                self.assertEqual(value.agency_id,self.target.pk,(model.__name__,field.name))
        self.assertFalse(PublicListing.objects.filter(property__agency=self.target,property__is_sample=True).exclude(status='draft').exists())
        sample_staff=User.objects.filter(membership__agency=self.target).exclude(pk=self.owner.pk)
        self.assertEqual(sample_staff.count(),10)
        self.assertFalse(sample_staff.filter(is_active=True).exists())
        self.assertTrue(all(not user.has_usable_password() for user in sample_staff))
        self.client.force_login(self.owner)
        page=self.client.get('/workspace/');self.assertContains(page,'SAMPLE DATA LOADED');self.assertEqual(page.context['stats'][0][1],26)
        prop=Property.objects.filter(agency=self.target,is_sample=True).first()
        from core.forms import scoped_form
        form=scoped_form(Property,AgencyMembership.objects.get(user=self.owner),instance=prop)
        payload={name:form[name].value() for name in form.fields if form[name].value() is not None}
        payload['name']='Edited through my workspace'
        response=self.client.post(f'/workspace/records/properties/{prop.pk}/edit/',payload)
        self.assertEqual(response.status_code,302,response.context and response.context['form'].errors)
        prop.refresh_from_db();self.assertEqual(prop.name,'Edited through my workspace');self.assertTrue(prop.is_sample)
        self.assertEqual(self.client.post(f'/workspace/publish/{prop.pk}/').status_code,302)
        self.assertContains(self.client.get(prop.get_absolute_url()),'Demonstration property')

    def test_repeat_import_preserves_edits_without_duplicates(self):
        self.copy()
        prop=Property.objects.filter(agency=self.target,is_sample=True).first()
        prop.name='My edited sample';prop.save()
        counts={m._meta.label:m.objects.count() for app in ['properties','management','crm'] for m in apps.get_app_config(app).get_models()}
        self.copy();prop.refresh_from_db();self.assertEqual(prop.name,'My edited sample')
        self.assertEqual(counts,{m._meta.label:m.objects.count() for app in ['properties','management','crm'] for m in apps.get_app_config(app).get_models()})
        self.assertEqual(DemoDataImport.objects.filter(agency=self.target).count(),1)

    def test_wrong_target_name_refused(self):
        with self.assertRaises(CommandError):
            call_command('copy_demo_to_agency',agency_id=self.target.pk,expected_name='Another Agency',stdout=io.StringIO())
        self.assertFalse(DemoDataImport.objects.exists())
        self.assertEqual(Property.objects.filter(agency=self.target).count(),1)

    def test_incomplete_source_rolls_back_without_partial_import(self):
        Property.objects.filter(slug='demo-property-25').update(archived=True)
        with self.assertRaises(CommandError): self.copy()
        self.assertFalse(DemoDataImport.objects.exists())
        self.assertEqual(Property.objects.filter(agency=self.target).count(),1)

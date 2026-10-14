"""Copy only known synthetic seed records to an existing agency, once.
Never clones enquiries, documents, uploaded media, usable accounts or real records.
"""
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import User
from django.db import transaction
from agencies.models import Agency,AgencyMembership
from core.models import DemoDataImport
from properties.models import Property,PublicListing
from management.models import Landlord,Tenant,PropertyUnit,Lease,Inspection,MaintenanceRequest,TransactionRecord
from crm.models import Lead,Viewing,Task,Contact
from core.services import refresh_occupancy

class Command(BaseCommand):
    help='Copy the original sample portfolio/operations/CRM into an existing agency as editable records.'

    def add_arguments(self,parser):
        parser.add_argument('--agency-id',type=int,required=True)
        parser.add_argument('--expected-name',required=True,help='Must match the target agency exactly.')

    @transaction.atomic
    def handle(self,*args,**options):
        try: target=Agency.objects.select_for_update().get(pk=options['agency_id'])
        except Agency.DoesNotExist: raise CommandError('Target agency does not exist.')
        if target.name!=options['expected_name']: raise CommandError('Agency name does not match; no records were copied.')
        if target.is_demo: raise CommandError('Choose a real agency workspace, not a source sample agency.')
        existing=DemoDataImport.objects.filter(agency=target).first()
        if existing:
            self.stdout.write('Sample data already imported; existing records and edits preserved.')
            return
        source_agencies=Agency.objects.filter(is_demo=True,name__in=['Coastal Living','Kilimanjaro Estates','Island & City'])
        if source_agencies.count()!=3: raise CommandError('The original three sample agencies must be seeded first.')
        sources=Property.objects.filter(agency__in=source_agencies,slug__startswith='demo-property-',archived=False)
        if sources.count()!=25: raise CommandError('Expected 25 original sample properties; refusing an incomplete import.')
        mapping={};manifest={}
        def remember(model,source_id,record):
            label=model._meta.label_lower
            mapping[(label,source_id)]=record.pk
            manifest.setdefault(label,{})[str(source_id)]=record.pk
        def clone(model,query):
            for source in query.order_by('pk'):
                data={}
                for field in model._meta.concrete_fields:
                    if field.primary_key or field.name in ['agency','created_at','updated_at','operation_id']:
                        continue
                    value=getattr(source,field.attname)
                    if field.is_relation:
                        if value is not None:
                            value=mapping.get((field.related_model._meta.label_lower,value))
                            if value is None: raise CommandError(f'Unmapped relation in synthetic {model.__name__}.{field.name}; import rolled back.')
                        data[field.attname]=value
                    else: data[field.name]=value
                data['agency']=target
                if model==Property:
                    data.update(slug=f'sample-agency-{target.pk}-{source.slug}',is_sample=True)
                if model==Lead: data['source']='Imported demo'
                if 'notes' in data:
                    data['notes']='[SAMPLE DATA — imported for demonstration]\n'+data['notes']
                if model==Inspection: data['photo']=''
                record=model.objects.create(**data)
                remember(model,source.pk,record)
        sample_usernames=['demo_admin','demo_manager','demo_agent']+[f'demo_agent{i}' for i in range(2,9)]
        staff=AgencyMembership.objects.filter(agency__in=source_agencies,user__username__in=sample_usernames).select_related('user')
        if staff.count()!=10: raise CommandError('Expected the original 10 sample staff profiles.')
        for source in staff:
            username=f'sample_a{target.pk}_{source.user.username}'
            if User.objects.filter(username=username).exists(): raise CommandError('A sample username already exists; import rolled back.')
            user=User.objects.create_user(username=username,first_name=source.user.first_name,last_name=source.user.last_name,email=f'{username}@example.invalid',is_active=False)
            member=AgencyMembership.objects.create(agency=target,user=user,role=source.role,phone=source.phone,specialization=source.specialization,verified=False)
            remember(AgencyMembership,source.pk,member)
        clone(Landlord,Landlord.objects.filter(agency__in=source_agencies,name__startswith='Sample Landlord ',archived=False))
        clone(Tenant,Tenant.objects.filter(agency__in=source_agencies,name__startswith='Sample Tenant ',archived=False))
        clone(Property,sources)
        for source in sources:
            PublicListing.objects.create(property_id=mapping[('properties.property',source.pk)],status='draft',verified=False,featured=False)
        clone(PropertyUnit,PropertyUnit.objects.filter(agency__in=source_agencies,property__in=sources,archived=False))
        clone(Lease,Lease.objects.filter(agency__in=source_agencies,unit__property__in=sources,tenant__name__startswith='Sample Tenant ',archived=False))
        clone(Inspection,Inspection.objects.filter(agency__in=source_agencies,property__in=sources,inspection_type='Sample routine inspection',archived=False))
        clone(MaintenanceRequest,MaintenanceRequest.objects.filter(agency__in=source_agencies,property__in=sources,description='Sample: check water pressure',archived=False))
        clone(TransactionRecord,TransactionRecord.objects.filter(agency__in=source_agencies,property__in=sources,reference__startswith='DEMO-',archived=False))
        leads=Lead.objects.filter(agency__in=source_agencies,source='Demo seed',name__startswith='Sample Customer ',archived=False)
        clone(Lead,leads)
        clone(Viewing,Viewing.objects.filter(agency__in=source_agencies,lead__in=leads,archived=False))
        clone(Task,Task.objects.filter(agency__in=source_agencies,lead__in=leads,archived=False))
        clone(Contact,Contact.objects.filter(agency__in=source_agencies,name__startswith='Sample Customer ',archived=False))
        refresh_occupancy(manifest.get('management.propertyunit',{}).values())
        DemoDataImport.objects.create(agency=target,manifest=manifest)
        self.stdout.write(self.style.SUCCESS(f'Editable sample data copied to {target.name} (agency {target.pk}).'))
        for label,ids in manifest.items(): self.stdout.write(f'{label}: {len(ids)}')
        self.stdout.write('All copied listings are drafts. Sample staff have disabled logins. No existing target records were replaced.')

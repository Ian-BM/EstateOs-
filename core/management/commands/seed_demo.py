from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from agencies.models import Agency,AgencyMembership
from properties.models import Property,PublicListing
from management.models import Landlord,Tenant,PropertyUnit,Lease,Inspection,MaintenanceRequest,TransactionRecord
from crm.models import Lead,Viewing,Task,Contact
from core.services import refresh_occupancy
class Command(BaseCommand):
    help='Create an idempotent LOCAL demo portfolio. Existing records and passwords are preserved.'
    @transaction.atomic
    def handle(self,*args,**options):
        if not settings.DEBUG: raise CommandError('Demo seeding is disabled when DEBUG is false.')
        now=timezone.now();today=timezone.localdate()
        agencies=[]
        for name,city in [('Coastal Living','Dar es Salaam'),('Kilimanjaro Estates','Arusha'),('Island & City','Zanzibar')]:
            agency,_=Agency.objects.get_or_create(name=name,is_demo=True,defaults={'city':city,'description':'Sample agency for the Estate OS demonstration.','phone':'+255 700 000 000','email':'demo@example.invalid'})
            agencies.append(agency)
        specs=[('demo_admin','admin','Amina','Mwakalinga',0),('demo_manager','manager','David','Mushi',0),('demo_agent','agent','Neema','Joseph',0),('demo_agent2','agent','Hassan','Ali',0),('demo_agent3','agent','Grace','Massawe',1),('demo_agent4','agent','James','Lema',1),('demo_agent5','agent','Fatma','Said',2),('demo_agent6','agent','Peter','Mollel',1),('demo_agent7','agent','Zainab','Omar',2),('demo_agent8','agent','Daniel','Mwinyi',0)]
        members=[]
        for username,role,first,last,index in specs:
            user,created=User.objects.get_or_create(username=username,defaults={'first_name':first,'last_name':last,'email':username+'@example.invalid'})
            if created: user.set_password('EstateDemo2026!');user.save()
            existing=AgencyMembership.objects.filter(user=user).first()
            if existing and (existing.agency_id!=agencies[index].pk or existing.role!=role): raise CommandError(f'Username {username} belongs to a different membership; refusing to overwrite.')
            member,_=AgencyMembership.objects.get_or_create(user=user,defaults={'agency':agencies[index],'role':role,'phone':'+255 700 000 000','specialization':['Coastal & luxury homes','Residential properties','Commercial spaces'][index]})
            members.append(member)
        owners=[]
        for i in range(10):
            agency=agencies[i%3]
            owner,_=Landlord.objects.get_or_create(agency=agency,name=f'Sample Landlord {i+1:02}',defaults={'phone':'+255 700 000 000','notes':'Demonstration record'})
            owners.append(owner)
        tenant_list=[]
        for i in range(15):
            tenant,_=Tenant.objects.get_or_create(agency=agencies[i%3],name=f'Sample Tenant {i+1:02}',defaults={'phone':'+255 700 000 000','notes':'Demonstration record'})
            tenant_list.append(tenant)
        cities=['Dar es Salaam','Zanzibar','Arusha','Dodoma']
        neighbourhoods=['Masaki','Nungwi','Njiro','Miyuji','Oyster Bay','Paje','Sakina','Nzuguni','Mikocheni','Stone Town','Kijenge','Kisasa']
        names=['Ocean-view Villa, Masaki','Masaki Residences, 3-Bed Apartment','Grade A Office Floor, Posta']
        types=['villa','apartment','office','house','land','studio','shop','warehouse','commercial']
        props=[]
        for i in range(25):
            agency=agencies[0] if i<3 else agencies[i%3]
            local_agents=[m for m in members if m.agency_id==agency.pk]
            ptype=types[i%len(types)]
            region='Dar es Salaam' if i<3 else cities[i%4]
            name=names[i] if i<3 else f'{["Garden","Coastal","Parkside","Sunset"][i%4]} {dict(Property.TYPES)[ptype]} · {neighbourhoods[i%12]}'
            price=[2450000000,6500000,28000000][i] if i<3 else (1800000+i*350000 if i%3 else 180000000+i*45000000)
            prop,_=Property.objects.get_or_create(slug=f'demo-property-{i+1:02}',defaults={'agency':agency,'name':name,'description':'A thoughtfully designed space with generous natural light, practical finishes and room to make it your own. Convenient access to local amenities and transport. This is a demonstration listing created for Estate OS, not real inventory. Contact the sample agency to explore how enquiries work.','property_type':ptype,'purpose':'sale' if i==0 or (i>2 and i%3==0) else 'rent','location':'Posta' if i==2 else ('Masaki' if i<2 else neighbourhoods[i%12]),'region':region,'address':'Sample address, Tanzania','price':price,'size':420 if i==0 else 140+i*15,'bedrooms':3 if ptype in ['villa','apartment','house'] else (1 if ptype=='studio' else 0),'bathrooms':2 if ptype not in ['land','warehouse'] else 0,'owner':next(o for o in owners if o.agency_id==agency.pk),'assigned_agent':local_agents[i%len(local_agents)],'assigned_manager':next((m for m in local_agents if m.role in ['admin','manager']),None),'features':'Natural light\nConvenient location\nFlexible living space\nSample amenities — verify with the agency','sample_image':f'property-{(i if i<3 else (i*5+i//6)%6)+1}.jpg'})
            listing,_=PublicListing.objects.get_or_create(property=prop,defaults={'status':'published' if i<22 else 'draft','published_at':now-timedelta(days=i%6,hours=i),'featured':i<3})
            props.append(prop)
            if ptype!='land':
                for j in range(2):
                    unit,_=PropertyUnit.objects.get_or_create(agency=agency,property=prop,identifier=f'{j+1:02}',defaults={'unit_type':'Apartment','floor':j,'size':90,'rental_amount':Decimal('900000')})
                    if j==0 and i<15:
                        tenant=next(t for t in tenant_list if t.agency_id==agency.pk)
                        Lease.objects.get_or_create(agency=agency,unit=unit,tenant=tenant,defaults={'start_date':today-timedelta(days=100),'end_date':today+timedelta(days=30+i*10),'monthly_rent':900000,'status':'active'})
                        refresh_occupancy([unit.pk])
            if i<9:
                Inspection.objects.get_or_create(agency=agency,property=prop,inspection_type='Sample routine inspection',defaults={'date':now+timedelta(days=i+1),'inspector':prop.assigned_agent,'notes':'Demonstration inspection'})
                MaintenanceRequest.objects.get_or_create(agency=agency,property=prop,description='Sample: check water pressure',defaults={'priority':'normal','assigned_person':prop.assigned_agent,'status':'open' if i%2 else 'in_progress'})
                TransactionRecord.objects.get_or_create(agency=agency,property=prop,reference=f'DEMO-{i+1:03}',defaults={'transaction_type':'rent','amount':900000,'payment_date':today-timedelta(days=i),'payment_method':'External bank transfer (sample)','verification_status':['pending','verified','rejected'][i%3],'notes':'Sample manual record. No money processed.'})
            if i<18:
                lead,_=Lead.objects.get_or_create(agency=agency,name=f'Sample Customer {i+1:02}',source='Demo seed',defaults={'phone':'+255 700 000 000','property':prop,'assigned_agent':prop.assigned_agent,'budget':price,'preferred_location':region,'status':Lead.STAGES[i%8][0],'follow_up_date':today+timedelta(days=i%5),'notes':'Illustrative customer record'})
                Contact.objects.get_or_create(agency=agency,name=lead.name,defaults={'phone':lead.phone,'notes':'Sample contact'})
                if i<10:
                    Viewing.objects.get_or_create(agency=agency,lead=lead,property=prop,defaults={'agent':prop.assigned_agent,'date':now+timedelta(days=i+1),'status':'confirmed' if i%2 else 'requested','notes':'Sample appointment'})
                Task.objects.get_or_create(agency=agency,lead=lead,title=f'Follow up with {lead.name}',defaults={'assigned_to':prop.assigned_agent,'property':prop,'deadline':now+timedelta(days=i%5+1)})
        self.stdout.write(self.style.SUCCESS('Demo portfolio ready: 3 agencies, 10 staff, 25 properties, 10 landlords, 15 tenants. Re-running preserves edits and does not duplicate seeded records.'))
        self.stdout.write('Local demo users: demo_admin / demo_manager / demo_agent. Initial password: EstateDemo2026! (existing passwords are not reset). No platform superuser is created.')

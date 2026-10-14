import csv,uuid
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction,IntegrityError
from django.db.models import Count,Q,Sum
from django.http import Http404,HttpResponse,FileResponse
from django.shortcuts import get_object_or_404,render,redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .permissions import membership,require_manager
from .registry import RECORDS,CRM_KEYS,MANAGEMENT_ONLY
from .forms import scoped_form
from .services import refresh_occupancy
from properties.models import Property,PublicListing,PropertyImage
from management.models import PropertyUnit,Tenant,Lease,Inspection,MaintenanceRequest,TransactionRecord,Document
from crm.models import Lead,Viewing,Task
from agencies.models import AgencyMembership


def info(request,page):
    if page not in ['about','pricing','contact','demo']: raise Http404
    return render(request,'public/info.html',{'page':page})

@login_required
def dashboard(request,section='management'):
    member=membership(request); agency=member.agency
    chart=[];occupancy_percent=0
    if section=='crm':
        leads=Lead.objects.filter(agency=agency,archived=False)
        views=Viewing.objects.filter(agency=agency,archived=False)
        stats=[('Total leads',leads.count()),('New enquiries',leads.filter(status='new').count()),('Awaiting follow-up',leads.exclude(status__in=['converted','lost']).filter(Q(follow_up_date__lte=timezone.localdate())|Q(follow_up_date=None)).count()),('Scheduled viewings',views.filter(status__in=['requested','confirmed'],date__gte=timezone.now()).count()),('Active agents',agency.memberships.filter(user__is_active=True).count()),('Converted leads',leads.filter(status='converted').count())]
        recent=leads.select_related('property','assigned_agent__user')[:6]
        total=leads.count()
        chart=[{'label':label,'count':leads.filter(status=stage).count(),'total':max(total,1)} for stage,label in Lead.STAGES]
    else:
        props=Property.objects.filter(agency=agency,archived=False)
        units=PropertyUnit.objects.filter(agency=agency,archived=False)
        stats=[('Total properties',props.count()),('Total units',units.count()),('Occupied units',units.filter(occupancy='occupied').count()),('Vacant units',units.filter(occupancy='vacant').count()),('Active tenants',Tenant.objects.filter(agency=agency,active=True,archived=False).count()),('Active leases',Lease.objects.filter(agency=agency,status='active',archived=False).count()),('Pending inspections',Inspection.objects.filter(agency=agency,status='pending',archived=False).count()),('Open maintenance',MaintenanceRequest.objects.filter(agency=agency,archived=False).exclude(status='resolved').count())]
        recent=props.select_related('listing')[:6]
        occupancy_percent=round(100*units.filter(occupancy='occupied').count()/units.count()) if units.count() else 0
    upcoming=Viewing.objects.filter(agency=agency,archived=False,date__gte=timezone.now(),status__in=['requested','confirmed']).order_by('date')[:5]
    inspections=Inspection.objects.filter(agency=agency,archived=False,status='pending').order_by('date')[:5]
    expiring=Lease.objects.filter(agency=agency,archived=False,status='active',end_date__range=[timezone.localdate(),timezone.localdate()+timedelta(days=60)]).select_related('tenant','unit')[:5]
    attention=Property.objects.filter(agency=agency,archived=False).filter(Q(listing__status='draft')|Q(maintenancerequest__status__in=['open','in_progress'])).distinct()[:5]
    activity=[]
    for key in (['leads','viewings','tasks'] if section=='crm' else ['properties','leases','maintenance','inspections']):
        for obj in RECORDS[key][0].objects.filter(agency=agency).order_by('-updated_at')[:3]:
            activity.append({'label':str(obj),'date':obj.updated_at,'kind':key})
    activity=sorted(activity,key=lambda x:x['date'],reverse=True)[:6]
    return render(request,'workspace/dashboard.html',{'section':section,'chart':chart,'occupancy_percent':occupancy_percent,'stats':stats,'recent':recent,'upcoming':upcoming,'inspections':inspections,'expiring':expiring,'attention':attention,'activity':activity,'title':'CRM overview' if section=='crm' else 'Portfolio overview'})

def record_config(request,key):
    if key not in RECORDS: raise Http404
    member=membership(request)
    if key in MANAGEMENT_ONLY: require_manager(member)
    return member,RECORDS[key]

@login_required
def record_list(request,key):
    member,(model,title,columns)=record_config(request,key)
    qs=model.objects.filter(agency=member.agency,archived=False)
    q=request.GET.get('q','')
    text_fields=[f.name for f in model._meta.fields if f.get_internal_type() in ['CharField','TextField']]
    if q:
        condition=Q()
        for name in text_fields: condition |= Q(**{name+'__icontains':q})
        qs=qs.filter(condition)
    if request.GET.get('status') and any(f.name=='status' for f in model._meta.fields): qs=qs.filter(status=request.GET['status'])
    if request.GET.get('export')=='csv':
        response=HttpResponse(content_type='text/csv');response['Content-Disposition']=f'attachment; filename="estate-os-{key}.csv"'
        writer=csv.writer(response);writer.writerow(columns)
        for obj in qs:
            values=[display(obj,c) for c in columns]
            writer.writerow([("'"+str(v)) if str(v).startswith(('=','+','-','@','\t','\r')) else v for v in values])
        return response
    page=Paginator(qs,20).get_page(request.GET.get('page'))
    rows=[{'object':obj,'cells':[{'label':c.replace('_',' ').title(),'value':display(obj,c)} for c in columns]} for obj in page]
    params=request.GET.copy();params.pop('page',None);params.pop('export',None)
    return render(request,'workspace/list.html',{'title':title,'key':key,'querystring':params.urlencode(),'columns':columns,'rows':rows,'page_obj':page,'section':'crm' if key in CRM_KEYS else 'management','stages':Lead.STAGES if key=='leads' else []})

def display(obj,name):
    method=getattr(obj,'get_'+name+'_display',None)
    value=method() if method else getattr(obj,name)
    return '—' if value is None or value=='' else value

@login_required
def record_detail(request,key,pk):
    member,(model,title,columns)=record_config(request,key)
    obj=get_object_or_404(model,pk=pk,agency=member.agency,archived=False)
    fields=[(f.verbose_name,display(obj,f.name)) for f in model._meta.fields if f.name not in ['id','agency','archived','operation_id','file']]
    return render(request,'workspace/detail.html',{'object':obj,'fields':fields,'key':key,'title':str(obj),'section':'crm' if key in CRM_KEYS else 'management','stages':Lead.STAGES,'units':obj.units.filter(archived=False) if key=='properties' else None,'viewings':obj.viewings.filter(archived=False) if key=='leads' else None,'associated_properties':Property.objects.filter(agency=member.agency,owner=obj,archived=False) if key=='landlords' else None,'related_leases':obj.leases.filter(archived=False).select_related('tenant','unit') if key in ['tenants','units'] else None})

@login_required
def record_edit(request,key,pk=None):
    member,(model,title,columns)=record_config(request,key)
    obj=get_object_or_404(model,pk=pk,agency=member.agency,archived=False) if pk else None
    if key=='inspections' and request.method=='POST' and request.POST.get('operation_id'):
        try: operation=uuid.UUID(request.POST['operation_id'])
        except ValueError: raise Http404
        existing=Inspection.objects.filter(operation_id=operation).first()
        if existing:
            if existing.agency_id!=member.agency_id: raise PermissionDenied
            messages.success(request,'This draft was already synchronized.')
            return redirect('record_detail',key=key,pk=existing.pk)
    else: operation=None
    form=scoped_form(model,member,request.POST if request.method=='POST' else None,request.FILES or None,instance=obj)
    if request.method!='POST':
        for field in ['property','lead']:
            if field in form.fields and request.GET.get(field):
                try: choice=form.fields[field].queryset.filter(pk=int(request.GET[field])).first()
                except (ValueError,OverflowError): choice=None
                if choice: form.initial[field]=choice.pk
    photo_form=None
    if key=='properties':
        from django import forms
        from .forms import validate_upload
        class PhotoForm(forms.Form):
            photo=forms.ImageField(required=False,validators=[validate_upload])
        photo_form=PhotoForm(request.POST if request.method=='POST' else None,request.FILES or None)
    if request.method=='POST' and form.is_valid() and (photo_form is None or photo_form.is_valid()):
        try:
            with transaction.atomic():
                old_unit=obj.unit_id if key=='leases' and obj else None
                record=form.save(commit=False);record.agency=member.agency
                if key=='properties' and not record.slug: record.slug=slugify(record.name)[:180]+'-'+uuid.uuid4().hex[:10]
                if key=='inspections' and operation: record.operation_id=operation
                record.save();form.save_m2m()
                if key=='properties':
                    listing,_=PublicListing.objects.get_or_create(property=record)
                    if member.role == 'agent' and listing.status == 'published':
                        listing.status='draft';listing.save(update_fields=['status'])
                    if photo_form.cleaned_data.get('photo'): PropertyImage.objects.create(property=record,image=photo_form.cleaned_data['photo'])
                if key=='leases': refresh_occupancy([old_unit,record.unit_id])
            messages.success(request,f'{model._meta.verbose_name.title()} saved successfully.')
            return redirect('record_detail',key=key,pk=record.pk)
        except IntegrityError:
            form.add_error(None,'A conflicting record already exists. Reload the page and check the selected unit or draft.')
    return render(request,'workspace/form.html',{'form':form,'photo_form':photo_form,'key':key,'title':('Edit ' if obj else 'Create ')+model._meta.verbose_name.title(),'section':'crm' if key in CRM_KEYS else 'management','offline':key=='inspections' and not pk})

@login_required
@require_POST
def archive(request,key,pk):
    member,(model,title,cols)=record_config(request,key)
    require_manager(member)
    obj=get_object_or_404(model,pk=pk,agency=member.agency)
    with transaction.atomic():
        obj.archived=True;obj.save(update_fields=['archived','updated_at'])
        if key=='properties':
            PublicListing.objects.filter(property=obj).update(status='draft')
        if key=='leases': refresh_occupancy([obj.unit_id])
    messages.success(request,'Record archived.')
    return redirect('record_list',key=key)

@login_required
@require_POST
def publish(request,pk):
    member=membership(request);require_manager(member)
    prop=get_object_or_404(Property,pk=pk,agency=member.agency,archived=False)
    listing,_=PublicListing.objects.get_or_create(property=prop)
    listing.status='draft' if request.POST.get('action')=='unpublish' else 'published'
    listing.approved_by=request.user
    if listing.status=='published': listing.published_at=timezone.now()
    listing.save()
    messages.success(request,'Listing '+listing.get_status_display().lower()+'.')
    return redirect('record_detail',key='properties',pk=pk)

@login_required
@require_POST
def lead_stage(request,pk):
    member=membership(request)
    lead=get_object_or_404(Lead,agency=member.agency,pk=pk,archived=False)
    if request.POST.get('status') not in dict(Lead.STAGES): raise Http404
    lead.status=request.POST['status'];lead.save(update_fields=['status','updated_at'])
    messages.success(request,'Lead stage updated.')
    return redirect('pipeline' if request.POST.get('pipeline') else reverse('record_detail',kwargs={'key':'leads','pk':pk}))

@login_required
def pipeline(request):
    member=membership(request)
    qs=Lead.objects.filter(agency=member.agency,archived=False).select_related('property','assigned_agent__user')
    columns=[{'key':k,'title':v,'leads':qs.filter(status=k)} for k,v in Lead.STAGES]
    return render(request,'workspace/pipeline.html',{'title':'Sales pipeline','section':'crm','pipeline_columns':columns,'stages':Lead.STAGES})

@login_required
def team(request,assignments=False):
    member=membership(request)
    agents=AgencyMembership.objects.filter(agency=member.agency).select_related('user').annotate(property_count=Count('properties',filter=Q(properties__archived=False),distinct=True),lead_count=Count('leads',filter=Q(leads__archived=False)&~Q(leads__status__in=['converted','lost']),distinct=True),viewing_count=Count('viewings',filter=Q(viewings__archived=False,viewings__status__in=['requested','confirmed'],viewings__date__gte=timezone.now()),distinct=True))
    props=Property.objects.filter(agency=member.agency,archived=False).select_related('assigned_agent__user') if assignments else []
    return render(request,'workspace/team.html',{'title':'Property assignments' if assignments else 'Your team','section':'crm','agents':agents,'assignments':props})

@login_required
def reports(request,performance=False):
    member=membership(request)
    if not performance: require_manager(member)
    if performance:
        rows=[]
        for agent in AgencyMembership.objects.filter(agency=member.agency).select_related('user'):
            rows.append([str(agent),agent.leads.filter(archived=False).count(),agent.viewings.filter(archived=False).count(),agent.viewings.filter(archived=False,status='completed').count(),agent.leads.filter(archived=False,status='converted').count(),agent.tasks.filter(archived=False,completed=False).count()])
        columns=['Agent','Assigned leads','Viewings','Completed viewings','Converted leads','Pending tasks']
    else:
        props=Property.objects.filter(agency=member.agency,archived=False)
        units=PropertyUnit.objects.filter(agency=member.agency,archived=False)
        rows=[['Properties','Total',props.count()],['Units','Occupied',units.filter(occupancy='occupied').count()],['Units','Vacant',units.filter(occupancy='vacant').count()]]
        for label,model,field in [('Leases',Lease,'status'),('Maintenance',MaintenanceRequest,'status'),('Transactions',TransactionRecord,'verification_status')]:
            for result in model.objects.filter(agency=member.agency,archived=False).values(field).annotate(total=Count('pk')): rows.append([label,result[field],result['total']])
        for result in TransactionRecord.objects.filter(agency=member.agency,archived=False).values('verification_status','transaction_type').annotate(total=Sum('amount')):
            rows.append(['TZS '+result['transaction_type'],result['verification_status'],result['total']])
        columns=['Report','Status / category','Count / TZS total']
    return render(request,'workspace/reports.html',{'title':'Team performance' if performance else 'Portfolio reports','section':'crm' if performance else 'management','rows':rows,'columns':columns,'performance':performance})

@login_required
def settings(request):
    member=membership(request);require_manager(member)
    from django.forms import modelform_factory
    Form=modelform_factory(type(member.agency),fields=['name','description','city','phone','email'])
    form=Form(request.POST or None,instance=member.agency)
    if request.method=='POST' and form.is_valid(): form.save();messages.success(request,'Agency settings updated.');return redirect('settings')
    return render(request,'workspace/form.html',{'title':'Agency settings','form':form,'section':'management'})

@login_required
def document_download(request,pk):
    member=membership(request);require_manager(member)
    doc=get_object_or_404(Document,pk=pk,agency=member.agency,archived=False)
    return FileResponse(doc.file.open('rb'),as_attachment=True,filename=doc.file.name.rsplit('/',1)[-1])


def property_image(request,pk):
    photo=get_object_or_404(PropertyImage.objects.select_related('property'),pk=pk)
    public=PublicListing.objects.filter(property=photo.property,status='published',property__archived=False).exists()
    if not public:
        if not request.user.is_authenticated: raise Http404
        member=membership(request)
        if member.agency_id!=photo.property.agency_id: raise Http404
    return FileResponse(photo.image.open('rb'),content_type='image/'+('jpeg' if photo.image.name.lower().endswith(('.jpg','.jpeg')) else 'webp' if photo.image.name.lower().endswith('.webp') else 'png'))

@login_required
def inspection_photo(request,pk):
    member=membership(request)
    obj=get_object_or_404(Inspection,pk=pk,agency=member.agency,archived=False)
    if not obj.photo: raise Http404
    return FileResponse(obj.photo.open('rb'))

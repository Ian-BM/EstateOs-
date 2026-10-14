from datetime import timedelta
from django.shortcuts import get_object_or_404,render,redirect
from django.db import transaction
from django.db.models import Q,Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from core.forms import EnquiryForm
from .models import Property,PublicListing,Enquiry
from agencies.models import Agency,AgencyMembership
from crm.models import Lead,Viewing

def published():
    return Property.objects.filter(archived=False,listing__status='published').select_related('agency','assigned_agent__user','listing').prefetch_related('images')

def home(request):
    all_props = published()
    locations = [{'name':name,'count':all_props.filter(region=name).count(),'image':f'location-{i+1}.jpg'} for i,name in enumerate(['Dar es Salaam','Zanzibar','Arusha','Dodoma'])]
    return render(request,'public/home.html',{'featured':all_props.filter(listing__featured=True).order_by('pk')[:3], 'recent':all_props.filter(listing__published_at__gte=timezone.now()-timedelta(days=7)).order_by('-listing__published_at')[:4], 'locations':locations,'agents':AgencyMembership.objects.select_related('user','agency').annotate(listing_count=Count('properties',filter=Q(properties__listing__status='published',properties__archived=False))).filter(agency__is_demo=True)[:4],'types':Property.TYPES})

def directory(request):
    qs = published()
    for key in ['purpose','region','property_type','availability']:
        value=request.GET.get(key)
        if value: qs=qs.filter(**{key:value})
    if request.GET.get('q'): qs=qs.filter(Q(name__icontains=request.GET['q'])|Q(location__icontains=request.GET['q'])|Q(region__icontains=request.GET['q']))
    for key,lookup in [('min_price','price__gte'),('max_price','price__lte'),('bedrooms','bedrooms__gte')]:
        value=request.GET.get(key,'')
        if value:
            try:
                from decimal import Decimal,InvalidOperation
                number=Decimal(value)
                if not number.is_finite() or number<0 or number>Decimal('99999999999999.99'): raise ValueError
                if key=='bedrooms' and (number>1000 or number!=number.to_integral_value()): raise ValueError
                qs=qs.filter(**{lookup:number})
            except (ValueError,InvalidOperation): messages.error(request,f'Invalid {key.replace("_"," ")}.');qs=qs.none()
    categories={'residential':['house','apartment','villa','studio'],'commercial':['office','shop','commercial','warehouse'],'land':['land']}
    if request.GET.get('category') in categories: qs=qs.filter(property_type__in=categories[request.GET['category']])
    sort={'price_low':'price','price_high':'-price','newest':'-listing__published_at'}.get(request.GET.get('sort'),'-listing__published_at')
    page=Paginator(qs.order_by(sort,'pk'),12).get_page(request.GET.get('page'))
    params=request.GET.copy();params.pop('page',None)
    return render(request,'public/directory.html',{'page_obj':page,'types':Property.TYPES,'querystring':params.urlencode(),'regions':published().order_by('region').values_list('region',flat=True).distinct()})

def detail(request,slug):
    prop=get_object_or_404(published(),slug=slug)
    form=EnquiryForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        last=request.session.get('last_enquiry',0)
        if timezone.now().timestamp()-last<30:
            form.add_error(None,'Please wait 30 seconds before sending another enquiry.')
        else:
            data=form.cleaned_data
            with transaction.atomic():
                lead=Lead.objects.create(agency=prop.agency,name=data['name'],phone=data['phone'],email=data['email'],property=prop,assigned_agent=prop.assigned_agent,notes=data['message'],source='Public directory')
                Enquiry.objects.create(listing=prop.listing,agency=prop.agency,lead=lead,**{key:data[key] for key in ['name','phone','email','message']})
                if data['request_viewing']:
                    # A request is not a confirmed appointment; staff arrange the date.
                    lead.notes+='\nViewing requested. Contact the customer to arrange a date.'
                    lead.save(update_fields=['notes'])
            request.session['last_enquiry']=timezone.now().timestamp()
            messages.success(request,'Enquiry sent. The agency will contact you'+(' to arrange your viewing.' if data['request_viewing'] else '.'))
            return redirect(prop)
    return render(request,'public/detail.html',{'property':prop,'form':form})

def professionals(request,kind,pk=None):
    if kind=='agents':
        qs=AgencyMembership.objects.select_related('agency','user').annotate(listing_count=Count('properties',filter=Q(properties__listing__status='published',properties__archived=False)))
    else: qs=Agency.objects.all()
    obj=get_object_or_404(qs,pk=pk) if pk else None
    listings=published().filter(**({'assigned_agent':obj} if kind=='agents' else {'agency':obj})) if obj else None
    return render(request,'public/professionals.html',{'kind':kind,'objects':qs if not obj else [],'object':obj,'listings':listings})

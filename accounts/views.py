from django.contrib.auth import login
from django.shortcuts import render,redirect
from django.db import transaction
from agencies.models import Agency,AgencyMembership
from .forms import RegistrationForm

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            agency = Agency.objects.create(name=form.cleaned_data['agency_name'],city=form.cleaned_data['city'],email=user.email)
            AgencyMembership.objects.create(user=user,agency=agency,role='admin')
        login(request,user)
        return redirect('workspace')
    return render(request,'accounts/form.html',{'form':form,'title':'Start your agency workspace','button':'Create account'})

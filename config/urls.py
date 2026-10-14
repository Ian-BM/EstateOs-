from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path,include
from core import views as ws
from properties import views as public
from accounts.views import register
urlpatterns = [
    path('',public.home,name='home'),
    path('properties/',public.directory,name='directory'),
    path('properties/<slug:slug>/',public.detail,name='property_detail'),
    path('agents/',public.professionals,{'kind':'agents'},name='agents'),
    path('agents/<int:pk>/',public.professionals,{'kind':'agents'},name='agent_detail'),
    path('agencies/',public.professionals,{'kind':'agencies'},name='agencies'),
    path('agencies/<int:pk>/',public.professionals,{'kind':'agencies'},name='agency_detail'),
    path('pricing/',ws.info,{'page':'pricing'},name='pricing'),
    path('about/',ws.info,{'page':'about'},name='about'),
    path('contact/',ws.info,{'page':'contact'},name='contact'),
    path('demo/',ws.info,{'page':'demo'},name='demo'),
    path('accounts/register/',register,name='register'),
    path('accounts/',include('django.contrib.auth.urls')),
    path('workspace/',ws.dashboard,name='workspace'),
    path('workspace/crm/',ws.dashboard,{'section':'crm'},name='crm_dashboard'),
    path('workspace/pipeline/',ws.pipeline,name='pipeline'),
    path('workspace/agents/',ws.team,name='team'),
    path('workspace/assignments/',ws.team,{'assignments':True},name='assignments'),
    path('workspace/performance/',ws.reports,{'performance':True},name='performance'),
    path('workspace/reports/',ws.reports,name='reports'),
    path('workspace/settings/',ws.settings,name='settings'),
    path('workspace/publish/<int:pk>/',ws.publish,name='publish'),
    path('workspace/leads/<int:pk>/stage/',ws.lead_stage,name='lead_stage'),
    path('workspace/documents/<int:pk>/download/',ws.document_download,name='document_download'),
    path('workspace/records/<slug:key>/',ws.record_list,name='record_list'),
    path('workspace/records/<slug:key>/new/',ws.record_edit,name='record_create'),
    path('workspace/records/<slug:key>/<int:pk>/',ws.record_detail,name='record_detail'),
    path('workspace/records/<slug:key>/<int:pk>/edit/',ws.record_edit,name='record_edit'),
    path('workspace/records/<slug:key>/<int:pk>/archive/',ws.archive,name='archive'),
    path('images/property/<int:pk>/',ws.property_image,name='property_image'),
    path('workspace/inspection-photo/<int:pk>/',ws.inspection_photo,name='inspection_photo'),
    path('admin/',admin.site.urls),
]

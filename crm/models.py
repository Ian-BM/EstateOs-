from django.db import models
from core.models import AgencyRecord
class Lead(AgencyRecord):
    STAGES = [('new','New Enquiry'),('contacted','Contacted'),('qualified','Qualified'),('scheduled','Viewing Scheduled'),('viewed','Viewing Completed'),('negotiation','Negotiation'),('converted','Converted'),('lost','Lost')]
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    property = models.ForeignKey('properties.Property',null=True,blank=True,on_delete=models.SET_NULL)
    assigned_agent = models.ForeignKey('agencies.AgencyMembership',null=True,blank=True,on_delete=models.SET_NULL,related_name='leads')
    budget = models.DecimalField(max_digits=16,decimal_places=2,null=True,blank=True)
    preferred_location = models.CharField(max_length=120,blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=40,default='Manual')
    status = models.CharField(max_length=14,choices=STAGES,default='new',db_index=True)
    follow_up_date = models.DateField(null=True,blank=True)
    def __str__(self): return self.name
class Viewing(AgencyRecord):
    property = models.ForeignKey('properties.Property',on_delete=models.CASCADE)
    lead = models.ForeignKey(Lead,on_delete=models.CASCADE,related_name='viewings')
    agent = models.ForeignKey('agencies.AgencyMembership',null=True,blank=True,on_delete=models.SET_NULL,related_name='viewings')
    date = models.DateTimeField()
    status = models.CharField(max_length=12,choices=[('requested','Requested'),('confirmed','Confirmed'),('completed','Completed'),('cancelled','Cancelled'),('no_show','No Show')],default='requested')
    notes = models.TextField(blank=True)
    def __str__(self): return f'{self.lead} · {self.property}'
class Task(AgencyRecord):
    title = models.CharField(max_length=180)
    assigned_to = models.ForeignKey('agencies.AgencyMembership',on_delete=models.SET_NULL,null=True,blank=True,related_name='tasks')
    deadline = models.DateTimeField()
    priority = models.CharField(max_length=10,choices=[('low','Low'),('normal','Normal'),('urgent','Urgent')],default='normal')
    completed = models.BooleanField(default=False)
    lead = models.ForeignKey(Lead,null=True,blank=True,on_delete=models.SET_NULL)
    property = models.ForeignKey('properties.Property',null=True,blank=True,on_delete=models.SET_NULL)
    def __str__(self): return self.title
class Contact(AgencyRecord):
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.name

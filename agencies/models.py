from django.conf import settings
from django.db import models
class Agency(models.Model):
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_demo = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    def __str__(self): return self.name
class AgencyMembership(models.Model):
    ROLES = [('admin','Agency Administrator'),('manager','Property Manager'),('agent','Real Estate Agent')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='membership')
    agency = models.ForeignKey(Agency,on_delete=models.CASCADE,related_name='memberships')
    role = models.CharField(max_length=12,choices=ROLES,default='agent')
    phone = models.CharField(max_length=40,blank=True)
    specialization = models.CharField(max_length=120,blank=True)
    verified = models.BooleanField(default=False)
    def __str__(self): return self.user.get_full_name() or self.user.username

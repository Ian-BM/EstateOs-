from django.db import models
from core.models import AgencyRecord
class Landlord(AgencyRecord):
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.name
class PropertyUnit(AgencyRecord):
    property = models.ForeignKey('properties.Property',on_delete=models.CASCADE,related_name='units')
    identifier = models.CharField(max_length=60)
    unit_type = models.CharField(max_length=80)
    floor = models.IntegerField(default=0)
    size = models.PositiveIntegerField()
    rental_amount = models.DecimalField(max_digits=14,decimal_places=2)
    occupancy = models.CharField(max_length=12,choices=[('vacant','Vacant'),('occupied','Occupied')],default='vacant')
    class Meta(AgencyRecord.Meta):
        constraints = [models.UniqueConstraint(fields=['property','identifier'],name='unique_property_unit'),models.CheckConstraint(condition=models.Q(rental_amount__gte=0),name='unit_rent_nonnegative')]
    def __str__(self): return f'{self.property.name} · {self.identifier}'
class Tenant(AgencyRecord):
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.name
class Lease(AgencyRecord):
    unit = models.ForeignKey(PropertyUnit,on_delete=models.PROTECT,related_name='leases')
    tenant = models.ForeignKey(Tenant,on_delete=models.PROTECT,related_name='leases')
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=14,decimal_places=2)
    status = models.CharField(max_length=12,choices=[('draft','Draft'),('active','Active'),('ended','Ended')],default='draft')
    class Meta(AgencyRecord.Meta):
        constraints = [models.CheckConstraint(condition=models.Q(end_date__gte=models.F('start_date')),name='lease_date_order'),models.CheckConstraint(condition=models.Q(monthly_rent__gte=0),name='lease_rent_nonnegative'),models.UniqueConstraint(fields=['unit'],condition=models.Q(status='active',archived=False),name='one_active_lease_per_unit')]
    def __str__(self): return f'{self.tenant} · {self.unit.identifier}'
class Inspection(AgencyRecord):
    property = models.ForeignKey('properties.Property',on_delete=models.CASCADE)
    inspector = models.ForeignKey('agencies.AgencyMembership',on_delete=models.SET_NULL,null=True,blank=True)
    date = models.DateTimeField()
    inspection_type = models.CharField(max_length=80,default='Routine')
    notes = models.TextField(blank=True)
    condition = models.CharField(max_length=20,choices=[('good','Good'),('fair','Fair'),('poor','Needs attention')],default='good')
    status = models.CharField(max_length=12,choices=[('pending','Pending'),('completed','Completed')],default='pending')
    photo = models.ImageField(upload_to='inspections/%Y/%m/',blank=True)
    operation_id = models.UUIDField(null=True,blank=True,unique=True,editable=False)
    def __str__(self): return f'{self.property} · {self.inspection_type}'
class MaintenanceRequest(AgencyRecord):
    property = models.ForeignKey('properties.Property',on_delete=models.CASCADE)
    unit = models.ForeignKey(PropertyUnit,on_delete=models.SET_NULL,null=True,blank=True)
    description = models.TextField()
    priority = models.CharField(max_length=10,choices=[('low','Low'),('normal','Normal'),('urgent','Urgent')],default='normal')
    assigned_person = models.ForeignKey('agencies.AgencyMembership',on_delete=models.SET_NULL,null=True,blank=True)
    status = models.CharField(max_length=12,choices=[('open','Open'),('in_progress','In progress'),('resolved','Resolved')],default='open')
    notes = models.TextField(blank=True)
    def __str__(self): return self.description[:70]
class TransactionRecord(AgencyRecord):
    property = models.ForeignKey('properties.Property',on_delete=models.PROTECT)
    tenant = models.ForeignKey(Tenant,on_delete=models.SET_NULL,null=True,blank=True)
    transaction_type = models.CharField(max_length=20,choices=[('rent','Rent'),('deposit','Deposit'),('expense','Expense'),('other','Other')])
    amount = models.DecimalField(max_digits=16,decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=80)
    reference = models.CharField(max_length=120,blank=True)
    notes = models.TextField(blank=True)
    verification_status = models.CharField(max_length=12,choices=[('pending','Pending verification'),('verified','Verified'),('rejected','Rejected')],default='pending')
    class Meta(AgencyRecord.Meta):
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=0),name='transaction_amount_nonnegative')]
    def __str__(self): return f'{self.get_transaction_type_display()} · TZS {self.amount:,.0f}'
class Document(AgencyRecord):
    property = models.ForeignKey('properties.Property',on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to='documents/%Y/%m/')
    def __str__(self): return self.title

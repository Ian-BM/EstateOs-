from django.db import models
from django.urls import reverse
from core.models import AgencyRecord
class Property(AgencyRecord):
    TYPES = [(x,x.title()) for x in ['house','apartment','villa','studio','office','shop','commercial','warehouse','land']]
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240,unique=True)
    description = models.TextField()
    property_type = models.CharField(max_length=20,choices=TYPES)
    purpose = models.CharField(max_length=8,choices=[('rent','For Rent'),('sale','For Sale')])
    location = models.CharField(max_length=120)
    region = models.CharField(max_length=100,db_index=True)
    address = models.CharField(max_length=240,blank=True)
    price = models.DecimalField(max_digits=16,decimal_places=2)
    size = models.PositiveIntegerField(help_text='Square metres')
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    owner = models.ForeignKey('management.Landlord',null=True,blank=True,on_delete=models.SET_NULL)
    assigned_agent = models.ForeignKey('agencies.AgencyMembership',null=True,blank=True,on_delete=models.SET_NULL,related_name='properties')
    assigned_manager = models.ForeignKey('agencies.AgencyMembership',null=True,blank=True,on_delete=models.SET_NULL,related_name='managed_properties')
    availability = models.CharField(max_length=15,choices=[('available','Available'),('occupied','Occupied'),('unavailable','Unavailable')],default='available')
    features = models.TextField(blank=True,help_text='One feature per line')
    sample_image = models.CharField(max_length=120,blank=True)
    is_sample = models.BooleanField(default=False,editable=False)
    class Meta(AgencyRecord.Meta):
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=0),name='property_price_nonnegative')]
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse('property_detail',args=[self.slug])
    @property
    def cover(self):
        photo = self.images.first()
        return reverse('property_image',args=[photo.pk]) if photo else '/static/images/'+(self.sample_image or 'property-1.jpg')
class PropertyImage(models.Model):
    property = models.ForeignKey(Property,on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to='properties/%Y/%m/')
    caption = models.CharField(max_length=180,blank=True)
class PublicListing(models.Model):
    property = models.OneToOneField(Property,on_delete=models.CASCADE,related_name='listing')
    status = models.CharField(max_length=12,choices=[('draft','Draft'),('published','Published')],default='draft',db_index=True)
    published_at = models.DateTimeField(null=True,blank=True)
    approved_by = models.ForeignKey('auth.User',null=True,blank=True,on_delete=models.SET_NULL)
    featured = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    def __str__(self): return str(self.property)
class Enquiry(models.Model):
    listing = models.ForeignKey(PublicListing,on_delete=models.CASCADE)
    agency = models.ForeignKey('agencies.Agency',on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    lead = models.OneToOneField('crm.Lead',on_delete=models.SET_NULL,null=True,related_name='enquiry')

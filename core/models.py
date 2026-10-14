from django.db import models
class AgencyRecord(models.Model):
    agency = models.ForeignKey('agencies.Agency',on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)
    class Meta:
        abstract = True
        ordering = ['-created_at']

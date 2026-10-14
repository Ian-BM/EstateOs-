from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from agencies.models import AgencyMembership
from management.models import Lease

def scoped_form(model, member, data=None, files=None, instance=None):
    excluded = ['agency','created_at','updated_at','archived','slug','sample_image','operation_id']
    if model._meta.model_name == 'transactionrecord' and member.role != 'admin':
        excluded.append('verification_status')
    class RecordForm(forms.ModelForm):
        class Meta:
            fields = '__all__'
            exclude = excluded
        def clean(self):
            cleaned = super().clean()
            for field in self.fields:
                val = cleaned.get(field)
                if hasattr(val,'agency_id') and val.agency_id != member.agency_id:
                    self.add_error(field,'Choose a record in your agency.')
            unit = cleaned.get('unit')
            prop = cleaned.get('property')
            if unit and prop and unit.property_id != prop.pk:
                self.add_error('unit','This unit does not belong to the selected property.')
            lead = cleaned.get('lead')
            if model._meta.model_name == 'viewing' and lead and prop and lead.property_id and lead.property_id != prop.pk:
                self.add_error('property','Select the property linked to this lead.')
            if model == Lease:
                start,end = cleaned.get('start_date'),cleaned.get('end_date')
                if start and end and end < start:
                    self.add_error('end_date','End date must follow start date.')
                if unit and cleaned.get('status') == 'active':
                    others = Lease.objects.filter(unit=unit,status='active',archived=False).exclude(pk=self.instance.pk)
                    if others.exists(): self.add_error('unit','This unit already has an active lease.')
            for name in ['price','rental_amount','monthly_rent','amount','budget']:
                if cleaned.get(name) is not None and cleaned[name] < 0:
                    self.add_error(name,'Amount must be zero or greater.')
            return cleaned
    RecordForm.Meta.model = model
    # ModelForm metaclass needs model at class creation.
    Meta = type('Meta',(),{'model':model,'fields':'__all__','exclude':excluded})
    Form = type('AgencyForm',(RecordForm,),{'Meta':Meta})
    form = Form(data=data,files=files,instance=instance)
    for name, field in form.fields.items():
        if isinstance(field,forms.ModelChoiceField):
            related = field.queryset.model
            if related == AgencyMembership:
                field.queryset = related.objects.filter(agency=member.agency)
                if name == 'assigned_manager': field.queryset = field.queryset.filter(role__in=['admin','manager'])
            elif any(f.name == 'agency' for f in related._meta.fields):
                field.queryset = related.objects.filter(agency=member.agency,archived=False)
        if isinstance(field,forms.DateTimeField): field.widget = forms.DateTimeInput(attrs={'type':'datetime-local'},format='%Y-%m-%dT%H:%M')
        elif isinstance(field,forms.DateField): field.widget = forms.DateInput(attrs={'type':'date'})
        if isinstance(field,forms.FileField):
            field.validators.append(validate_upload)
        if isinstance(field,forms.CharField) and isinstance(field.widget,forms.Textarea): field.widget.attrs['rows']=4
    return form

def validate_upload(file):
    if file.size > 5*1024*1024: raise ValidationError('Maximum upload size is 5 MB.')
    from pathlib import Path
    if Path(file.name).suffix.lower() not in ['.jpg','.jpeg','.png','.webp','.pdf']:
        raise ValidationError('Upload a JPEG, PNG, WebP or PDF file.')
    if Path(file.name).suffix.lower() == '.pdf':
        header = file.read(5); file.seek(0)
        if header != b'%PDF-': raise ValidationError('Invalid PDF file.')

class EnquiryForm(forms.Form):
    name = forms.CharField(max_length=120)
    phone = forms.RegexField(regex=r'^\+?[0-9 ()-]{7,25}$',max_length=40)
    email = forms.EmailField(required=False)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows':4}),max_length=5000)
    website = forms.CharField(required=False,widget=forms.HiddenInput)
    request_viewing = forms.BooleanField(required=False,label='Request a viewing — the agent will confirm a time')
    def clean_website(self):
        if self.cleaned_data['website']: raise ValidationError('Unable to submit this enquiry.')
        return ''

from agencies.models import AgencyMembership

def workspace(request):
    member = AgencyMembership.objects.select_related('agency').filter(user=request.user).first() if request.user.is_authenticated else None
    return {'current_member':member}

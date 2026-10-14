from agencies.models import AgencyMembership

def workspace(request):
    member = AgencyMembership.objects.select_related('agency','agency__sample_import').filter(user=request.user).first() if request.user.is_authenticated else None
    return {'current_member':member,'has_imported_samples':bool(member and getattr(member.agency,'sample_import',None))}

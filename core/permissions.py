from django.core.exceptions import PermissionDenied
from agencies.models import AgencyMembership

def membership(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    member = AgencyMembership.objects.select_related('agency','user').filter(user=request.user).first()
    if not member:
        raise PermissionDenied('An agency membership is required. Platform administrators manage all agencies through /admin/.')
    return member

def require_manager(member):
    if member.role not in ('admin','manager'):
        raise PermissionDenied('Only agency administrators and property managers can perform this action.')

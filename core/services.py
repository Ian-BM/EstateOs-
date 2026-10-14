from management.models import PropertyUnit,Lease

def refresh_occupancy(unit_ids):
    for pk in set(unit_ids):
        if pk:
            PropertyUnit.objects.filter(pk=pk).update(occupancy='occupied' if Lease.objects.filter(unit_id=pk,status='active',archived=False).exists() else 'vacant')

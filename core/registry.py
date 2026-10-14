from properties.models import Property
from management.models import Landlord,PropertyUnit,Tenant,Lease,Inspection,MaintenanceRequest,TransactionRecord,Document
from crm.models import Lead,Viewing,Task,Contact
RECORDS = {
'properties':(Property,'Properties',['name','region','purpose','availability']),
'units':(PropertyUnit,'Units',['identifier','property','rental_amount','occupancy']),
'landlords':(Landlord,'Landlords',['name','phone','email']),
'tenants':(Tenant,'Tenants',['name','phone','email','active']),
'leases':(Lease,'Leases',['tenant','unit','end_date','monthly_rent','status']),
'inspections':(Inspection,'Inspections',['property','date','inspector','status']),
'maintenance':(MaintenanceRequest,'Maintenance',['property','description','priority','status']),
'financial-records':(TransactionRecord,'Financial records',['property','amount','payment_date','verification_status']),
'documents':(Document,'Documents',['title','property']),
'leads':(Lead,'Leads',['name','property','assigned_agent','status','follow_up_date']),
'viewings':(Viewing,'Viewings',['lead','property','agent','date','status']),
'tasks':(Task,'Tasks',['title','assigned_to','deadline','priority','completed']),
'contacts':(Contact,'Contacts',['name','phone','email']),
}
CRM_KEYS=['leads','viewings','tasks','contacts']
MANAGEMENT_ONLY=['units','landlords','tenants','leases','maintenance','financial-records','documents']

from core.models import ObjectType
from extras.validators import CustomValidator
from netbox.context import current_request
from dcim.models import Location, Device, Site, SiteGroup, Region, Rack, Device
from ipam.models import Prefix
from django.db.models import Q
import re
from sop_compliance.report_loggers import CheckResult, CheckResultList, ValidatorCheckResultLogger
from sop_infra.utils.meraki_objects import MerakiConstants
from extras.choices import LogLevelChoices
from sop_infra.utils.netbox_utils import SopInfraUtils, SopInfraConstants
from sop_utils.misc import SopUtils


locations_ignored_by_status = ['planned', 'retired']
devices_ignored_by_status = ['planned', 'inventory', 'offline']
racks_ignored_by_status = ['planned', 'retired']

class DeviceRules:

    @staticmethod
    def check_one_device_location(device:Device, crl:CheckResultList): 
        if device.status in devices_ignored_by_status:
            return
        if device.location is None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, device,f"{device.site.group.name}:{device.name} : this device is missing a valid location", "location"))
    @staticmethod
    def check_devices_location(crl:CheckResultList): 
        for device in Device.objects.all():
            DeviceRules.check_one_device_location(device, crl)

    @staticmethod
    def check_one_device_tenancy(device:Device, crl:CheckResultList):
        if device.status in devices_ignored_by_status:
            return
        if device.tenant is None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, device, f"{device.site.group.name}:{device.name} : this device is missing a tenant", "tenant"))
        elif device.tenant!=device.site.tenant:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, device, f"{device.site.group.name}:{device.name} : this device tenant and its site tenant do not match !", "tenant"))
    @staticmethod
    def check_devices_tenancy(crl:CheckResultList):
        for device in Device.objects.all():
            DeviceRules.check_one_device_tenancy(device, crl)
        
            
    @staticmethod
    def check_one_device_status(device:Device, crl:CheckResultList):
        if device.site.status in [ 'retired']:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, device,
                                   f"{device.site.group.name}:{device.name} : cannot have devices on \"{device.site.status}\" sites !", "site"))
        elif device.site.status in ['test', 'teleworker', 'template', 'dc', 'no_infra',  'staging', 'inventory', 'reserved']:
            pass
        elif device.site.status in [ 'starting', 'active', 'decommissioning', 'test-poc']:
            if device.status in ['staged', 'planned']:
                crl.append(CheckResult(LogLevelChoices.LOG_WARNING, device,
                    f"{device.site.group.name}:{device.name} on site  [{device.site.name}]({device.site.get_absolute_url()}): this device should be \"active\" on this \"{device.site.status}\" site, not \"{device.status}\" !", "site"))
            elif device.status not in ['active', 'decommissioning', 'offline', 'failed']:
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, device,
                    f"{device.site.group.name}:{device.name} on site  [{device.site.name}]({device.site.get_absolute_url()}): only ['active', 'decommissioning', 'offline', 'failed'] devices can be on \"{device.site.status}\" sites !", "site"))
        else:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, device,
                f"{device.site.group.name}:{device.name} : Validator logic bug for site status \"{device.site.status}\"", "site"))      
    @staticmethod
    def check_devices_status(crl:CheckResultList):
        for device in Device.objects.all():
            DeviceRules.check_one_device_status(device, crl)


class OrgRules:

    site_ct=ObjectType.objects.get_by_natural_key('dcim', 'site')  

    @staticmethod
    def check_one_sdwanslave_is_empty(site:Site, crl:CheckResultList):
        if SopInfraUtils.get_sopinfra_site_master_site_id(site) is None:
            return
        if site.devices.first() or site.racks.first() or site.locations.first() or site.prefixes.first():
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} : this site is an SDWAN slave but it's not empty !"))
    @staticmethod
    def check_sdwanslaves_are_empty(crl:CheckResultList):
        for site in Site.objects.all():
            OrgRules.check_one_sdwanslave_is_empty(site, crl)

    @staticmethod
    def check_one_retired_site_is_empty(site:Site, crl:CheckResultList):
        if site.status != "retired":
            return
        if Device.objects.filter(site_id=site.pk).exclude(status='offline').exists() or \
            Location.objects.filter(site_id=site.pk).exclude(status='retired').exists() or \
            Prefix.objects.filter(scope_type=OrgRules.site_ct).filter(scope_id=site.pk).exclude(status='retired').exists() or \
            Rack.objects.filter(site_id=site.pk).exclude(status='retired').exists() :
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"This site is retired but it's not empty !", field='status'))
    @staticmethod
    def check_retired_sites_are_empty(crl:CheckResultList):
        for site in Site.objects.all():
            OrgRules.check_one_retired_site_is_empty(site, crl)

    @staticmethod
    def check_one_site_tenancy(site:Site, crl:CheckResultList):
        if site.tenant is None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"This site is missing a valid tenant !", field='tenant')) 
        if site.tenant is None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"This site is missing a valid tenant !", field='tenant')) 
    @staticmethod
    def check_sites_tenancy(crl:CheckResultList):
        for site in Site.objects.all():
            OrgRules.check_one_site_tenancy(site, crl)

    @staticmethod
    def check_one_site_tz(site:Site, crl:CheckResultList):
        if site.status not in ['reserved', 'template', 'inventory', 'test', 'retired']  :
            if site.time_zone is None :
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} : this site is missing a timezone definition", field='time_zone'))
    @staticmethod
    def check_sites_tz(crl:CheckResultList):
        for site in Site.objects.all():
            OrgRules.check_one_site_tz(site, crl)

    @staticmethod
    def check_one_site_status(site:Site, crl:CheckResultList):
        sts=""
        if site.tenant is not None :
            sts=site.tenant.cf.get('tenant_status',"")
        if sts == "candidate":
            if site.status in ['starting','staging','active','decommissioning']:
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" sites cannot be on \"{sts}\" tenant status !", field='status'))                
        elif sts == "retired":
            if site.status not in ['retired']:
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" sites cannot be on \"{sts}\" tenant status !", field='status'))                
        if site.status in ['no_infra']:
            if site.prefixes.exclude(vrf=None).exists() :
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" sites cannot have non local VRF prefixes !", field='status'))           
    @staticmethod
    def check_sites_statuses(crl:CheckResultList):
        for site in Site.objects.all():
            OrgRules.check_one_site_status(site, crl)

    @staticmethod
    def check_one_site_address(site:Site, crl:CheckResultList):
        address_needed= (site.status not in ['reserved', 'template', 'inventory', 'test', 'retired', 'no_infra'] ) 
        address_forbidden=(site.status in ['template', 'inventory'])
        if address_needed and (site.physical_address is None or site.physical_address.strip() =='') :
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" mandates an address", field='physical_address'))
        if address_forbidden and (site.physical_address is not None and site.physical_address.strip() !='') :
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" forbids an address", field='physical_address'))
        if address_needed and not re.match("^([^\n]* \r?\n)+[^\n]+$", site.physical_address) :
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  Address must be multiline and each line must end with a space", field='physical_address'))
        if address_needed and (site.latitude is None or site.latitude==0):
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" mandates latitude", field='latitude'))
        if address_needed and (site.longitude is None or site.longitude==0):
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" mandates longitude", field='longitude'))
        if address_forbidden and site.latitude is not None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" forbids latitude", field='latitude'))
        if address_forbidden and site.longitude is not None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} :  \"{site.status}\" forbids longitude", field='longitude'))
    @staticmethod
    def check_sites_addresses(crl:CheckResultList):
        for site in Site.objects.all():
            OrgRules.check_one_site_address(site, crl)




    @staticmethod
    def check_one_location_tenancy(location:Location, crl:CheckResultList):
        if  location.status in locations_ignored_by_status:
            return
        if location.tenant is None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, location, f"{location.site.group.name}:{location.name} : this location is missing a valid tenant !"))    
        elif location.tenant != location.site.tenant:
            if not(location.site.custom_field_data.get('site_multi_tenant', False)):    
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, location, f"{location.site.group.name}:{location.name} : this location tenant doesn't match the site tenant"))    
    @staticmethod
    def check_locations_tenancy(crl:CheckResultList):
        for location in Location.objects.all():
            OrgRules.check_one_location_tenancy(location, crl)

    @staticmethod
    def check_one_location_name(location:Location, crl:CheckResultList):
        if  location.status in locations_ignored_by_status:
            return
        if location.tenant is None or location.tenant.name != "SOPIT" :
            if location.parent is not None:
                if not location.name.startswith(location.parent.name + " - "):
                    crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, location, f"{location.site.group.name}:{location.name} : this location name must begin with \"{location.parent.name} - \"", "name"))
            elif location.name != location.site.name:
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, location, f"{location.site.group.name}:{location.name} : this root location name must \"{location.site.name}\"", "name"))
    @staticmethod
    def check_locations_names(crl:CheckResultList):
        for location in Location.objects.all():
            OrgRules.check_one_location_name(location, crl)




class SiteValidator(CustomValidator):

    valid_status_changes={ 
        "reserved" : (),
        "no_infra" : (),
        "staging" : ('no_infra'),
        "starting" : ('staging', 'active'),
        "active" : ('starting'),
        "decommissioning" : ('active', 'starting', 'staging', ),
        "retired" : ('decommissioning', 'no_infra')
    }
    
    creation_status = ('no_infra', 'staging')
    staff_status = ('dc', 'template', 'inventory', 'teleworker', 'test-poc', 'reserved')


    def validate(self, instance, request):

        crl=CheckResultList()
        site:Site=instance
        if site.description=="debug":
            site.comments=f"{site.tags.slugs()} - DEBUG : {site.status} -- {site.physical_address} -- {vars(site)} "
        if site.description=="debugstop":
            self.fail(f"DEBUG : {site.status} -- {site.physical_address} -- {vars(site)}  ")
        if site.description=="debugfull":
            site.comments=f"DEBUG : {site.status} -- {site.physical_address} -- {vars(site)} \n -- REQUEST : {vars(request)}"
        if site.description=="debugstopfull":
            self.fail(f"DEBUG : {site.status} -- {site.physical_address} -- {vars(site)}  \n -- REQUEST : {vars(request)}")



        resUrlName = ''
        if request is not None and hasattr(request, "resolver_match") and hasattr(request.resolver_match, "url_name"):
            resUrlName = request.resolver_match.url_name

        failprefix=""
        if  resUrlName=='site_bulk_edit':
            failprefix=f"{site.slug} -> "


        # Workflow checks
        staff=SopUtils.is_staff_user(request)
        pre_status:str|None=None
        if  site.pk is not None and hasattr(site, '_prechange_snapshot'):
            pre_status=site._prechange_snapshot.get('status')
        self.wf_validate_status_change(staff, pre_status, site.status, site, failprefix)

        # Fix physical address line endings
        if site.physical_address is not None and not re.match("^([^\n]* \r?\n)+[^\n]+$", site.physical_address):
            padd=""
            for ln in site.physical_address.splitlines():
                padd += ln.strip()+" \n"
            site.physical_address=padd



        # Check group
        if site.status in ['reserved', 'template', 'inventory', 'test'] :
            site.group=SiteGroup.objects.filter(slug="special")[0]
        elif site.status in ['dc'] :
            dcs=SiteGroup.objects.filter(slug="dcs")[0]
            match=False
            for sdcs in dcs.get_descendants():
                if site.group==sdcs:
                    match=True
                    break
            if not match:
                site.group=dcs
        else:
            if site.group is None :
                self.fail(f"{failprefix}Status '{site.status}' mandates a group definition", field='group')
            if SiteGroup.objects.filter(parent=site.group).count()>0 :
                self.fail(f"{failprefix}Only leaf groups are allowed", field='group')
            if site.group.get_root().id!=SopInfraConstants.spokes_root_id:
                self.fail(f"{failprefix}Status '{site.status}' needs a spoke site group", field='group') 

        # Check address / latitude / longitude compliance
        OrgRules.check_one_site_address(site, crl)

        # Check region
        if site.status not in ['reserved', 'template', 'inventory', 'test']  :
            if site.region is None :
                self.fail(f"{failprefix}Status '{site.status}' mandates a region definition", field='region')
            if Region.objects.filter(parent=site.region).count()>0 :
                self.fail(f"{failprefix}Only leaf regions are allowed", field='region')

        # Check TZ
        OrgRules.check_one_site_tz(site, crl)
        # Mandatory tenant
        OrgRules.check_one_site_tenancy(site, crl)

        # TODO check that the NDI is unique

        # DC special case
        if site.status == "dc":
            pass

        # Enforce slave site constraints
        elif SopInfraUtils.get_sopinfra_site_master_site_id(site) is not None :    
            # Resets some fields
            site.custom_field_data['sharepoint_subdir'] = None

        # Enforce non slave site constraints
        else :

            # Non slave sites = mandatory sharepoint subdir
            if site.custom_field_data['sharepoint_subdir'] is None and site.status not in ['reserved', 'template', 'inventory', 'teleworker', 'test', 'retired']:
                self.fail(f"{failprefix}Sharepoint subdir is mandatory for non slave sites", field='cf_sharepoint_subdir')
           

        crl.dump_to(ValidatorCheckResultLogger(self, failprefix))
        

    def wf_validate_status_change(self, is_staff:bool, prev:str|None, new:str|None, site:Site, failprefix:str):
        if new is None or new.strip()=="":
            self.fail(f"{failprefix} validator bug : new status is empty", field='status')
            return
        # Initial creation or change ?
        if prev is None or prev.strip()=="":
            # INITIAL CREATION --> Only allow some status
            if site.status in self.creation_status:
                pass
            elif is_staff and site.status in self.staff_status:
                pass 
            else: 
                self.fail(f"{failprefix} workflow exception : invalid status {site.status}", field='status')           
                return
        elif prev.strip()!=new.strip():
            # STATUS CHANGE DETECTED --> check rules
            # Staff can set any status
            if not is_staff:
                if new == "active":
                    self.fail(f"You do not have 'active' setting privilege", field='status')
                    return
                # For others, we check by target status
                validprev=self.valid_status_changes.get(new)
                if validprev is None:
                    self.fail(f"{failprefix} validator bug : unknown new status {new}", field='status')
                    return               
                elif not prev in validprev:
                    self.fail(f"{failprefix} workflow exception : cannot change status from {prev} to {new}  (allowed={validprev})", field='status')
                    return
            # Make sure we don't have any devices left on the site before retiring it
            if "retired"==new and site.pk is not None and Device.objects.filter(site=site).count()>0:
                self.fail(f"{failprefix} workflow exception : cannot retire a site that still has devices", field='status')
            # TODO : check that the site matches other workflow rules



# ========================================================================================

class DeviceValidator(CustomValidator):
    def validate(self, instance:Device, request):
        failprefix=f"{instance.name} -> "   
        crl=CheckResultList()
        DeviceRules.check_one_device_tenancy(instance, crl)
        DeviceRules.check_one_device_status(instance, crl)
        crl.dump_to(ValidatorCheckResultLogger(self, failprefix))



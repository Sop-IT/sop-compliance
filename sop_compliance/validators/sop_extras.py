import re

from django.contrib.contenttypes.models import ContentType

from extras.models import ImageAttachment
from extras.choices import LogLevelChoices

from extras.choices import LogLevelChoices

from extras.validators import CustomValidator

from dcim.models import Site, Location, Rack
from utilities.permissions import get_permission_for_model
from sop_compliance.report_loggers import CheckResult, CheckResultList
from sop_infra.utils.netbox_utils import SopInfraUtils
from sop_utils.regexps import SopRegExps

class ExtraRules():

    class Constants:
        ctype_site=31
        ctype_location=30
        ctype_rack=29
    
    class RegExps():
        google_image_str=r'^' + SopRegExps.date_str + r' - GOOGLE$'
        google_image_re=re.compile(google_image_str)
        rack_image_str=r'^' + SopRegExps.date_str + r' - .*$'
        rack_image_re=re.compile(rack_image_str)

    @staticmethod
    def check_one_site_has_mandatory_image_attachments(site:Site, crl:CheckResultList):
        if site.status in ['reserved', 'candidate', 'no_infra', 'dc', 'template', 'inventory', 'teleworker', 'test-poc', 'retired']:
            return
        cnt=ImageAttachment.objects.filter(object_type_id=ExtraRules.Constants.ctype_site)\
            .filter(object_id=site.pk).filter(name__regex=ExtraRules.RegExps.google_image_str).count()
        target_cnt=1
        if SopInfraUtils.get_sopinfra_site_master_site_id(site) is not None:
            target_cnt=0
            crl.append(CheckResult(LogLevelChoices.LOG_DEBUG, site, f"{site.group.name}:{site.name} : sdwan master site detected : {SopInfraUtils.get_sopinfra_site_master_site_id(site)}"))
        if cnt<target_cnt:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} : this site is missing a proper GOOGLE map !"))
        elif cnt>target_cnt:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} : this site has too many GOOGLE maps !"))
    @staticmethod
    def check_sites_have_mandatory_image_attachments(crl:CheckResultList):
        for site in Site.objects.all():
            ExtraRules.check_one_site_has_mandatory_image_attachments(site, crl)

    @staticmethod
    def check_one_location_has_mandatory_image_attachments(location:Location, crl:CheckResultList):
        if location.status in [ 'retired']:
            return
        cnt=ImageAttachment.objects.filter(object_type_id=ExtraRules.Constants.ctype_location)\
            .filter(object_id=location.pk).filter(name__regex=ExtraRules.RegExps.google_image_str).count()
        if cnt==0:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, location, f"{location.site.group.name}:{location.name} : this location is missing a proper GOOGLE map !"))
        elif cnt>1:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, location, f"{location.site.group.name}:{location.name} : this location has too many GOOGLE maps !"))
    @staticmethod
    def check_locations_have_mandatory_image_attachments(crl:CheckResultList):
        for location in Location.objects.all():
            ExtraRules.check_one_location_has_mandatory_image_attachments(location, crl)

    @staticmethod
    def check_one_rack_has_mandatory_image_attachments(rack:Rack, crl:CheckResultList):
        if rack.status in [ 'retired']:
            return
        cnt=ImageAttachment.objects.filter(object_type_id=ExtraRules.Constants.ctype_rack)\
            .filter(object_id=rack.pk).filter(name__regex=ExtraRules.RegExps.rack_image_str).count()
        if cnt==0:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, rack, f"{rack.site.group.name}:{rack.name} : this rack is missing images !"))
    @staticmethod
    def check_racks_have_mandatory_image_attachments(crl:CheckResultList):
        for rack in Rack.objects.all():
            ExtraRules.check_one_rack_has_mandatory_image_attachments(rack, crl)


# ========================================================================================

class ImageAttachmentValidator(CustomValidator):


    def validate(self, instance:ImageAttachment, request):
        if instance.object_type.pk == ContentType.objects.get_by_natural_key('dcim', 'site').pk:
            # Sites
            if not ExtraRules.RegExps.google_image_re.match(instance.name):
                self.fail(f'Icorrect name {instance.name}, must match "{ExtraRules.RegExps.google_image_re.pattern}" !', field='name')
        elif instance.object_type.pk == ContentType.objects.get_by_natural_key('dcim', 'location').pk:
            # Locations
            if not ExtraRules.RegExps.google_image_re.match(instance.name):
                self.fail(f'Icorrect name {instance.name}, must match "{ExtraRules.RegExps.google_image_re.pattern}" !', field='name')
        elif instance.object_type.pk == ContentType.objects.get_by_natural_key('dcim', 'rack').pk:
            # Racks
            if not ExtraRules.RegExps.rack_image_re.match(instance.name):
                self.fail(f'Icorrect name {instance.name}, must match "{ExtraRules.RegExps.rack_image_re.pattern}" !', field='name')




# ========================================================================================

class NetboxAttachmentValidator(CustomValidator):

    date_reg_str=r'^20[0-2][0-9]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])'
    locs_and_sites=[ ContentType.objects.get_by_natural_key('dcim', 'site').pk, ContentType.objects.get_by_natural_key('dcim', 'location').pk ]
    circuits=[ ContentType.objects.get_by_natural_key('circuits', 'circuit').pk ]
    devtypes=[ ContentType.objects.get_by_natural_key('dcim', 'devicetype').pk ]
    validators = [
        { "ctype":devtypes, "groups" : ["ALL_ITA_Netbox_Team_Network"], "file" : re.compile(r'^.*$'), "name" : re.compile(r'^.*$') },
        { "ctype":circuits, "groups" : ["ALL_ITA_Netbox_Team_Network"], "file" : re.compile(r'^.*$'), "name" : re.compile(date_reg_str + r' - .*$') },
        { "ctype":circuits, "groups" : ["ALL_ITA_Netbox_Team_Integration"], "file" : re.compile(r'^.*$'), "name" : re.compile(date_reg_str + r' - .*$') },
        { "ctype":locs_and_sites, "groups" : ["ALL_ITA_Netbox_Role_DCIM_Location_Manager", "ALL_ITA_Netbox_Team_Integration"], "file" : re.compile(r'^.*\.(?i:greenshot)$'), "name" : re.compile(date_reg_str + r' - (GOOGLE)(| - .+)$') },
        { "ctype":locs_and_sites, "groups" : ["ALL_ITA_Netbox_Role_DCIM_Location_Manager", "ALL_ITA_Netbox_Team_Integration"], "file" : re.compile(r'^.*\.(?i:pdf)$'), "name" : re.compile(date_reg_str + r' - (WIFI COVERAGE STUDY|PDF PLAN|DUDE L2)(| - .+)$')},
        { "ctype":locs_and_sites, "groups" : ["ALL_ITA_Netbox_Role_DCIM_Location_Manager", "ALL_ITA_Netbox_Team_Integration"], "file" : re.compile(r'^.*\.(?i:dwg)$'), "name" : re.compile(date_reg_str + r' - (DWG PLAN)(| - .+)$')},
        { "ctype":locs_and_sites, "groups" : ["ALL_ITA_Netbox_Role_DCIM_Location_Manager", "ALL_ITA_Netbox_Team_Integration"], "file" : re.compile(r'^.*\.(?i:pdn)$'), "name" : re.compile(date_reg_str + r' - (Multilayer MAP)(| - .+)$') },
        { "ctype":locs_and_sites, "groups" : ["ALL_ITA_Netbox_Team_Network"], "file" : re.compile(r'^.*$'), "name" : re.compile(date_reg_str + r' - .*$')}
    ]

    rack_image_reg=re.compile(r'^20[0-2][0-9]-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) - .*$')

    def validate(self, instance, request):
        debug=""
        user = request.user
        groups = list(user.groups.values_list('name', flat = True))
        vals = []
        if instance.description=="debug":
             debug=debug+f"\n - groups={groups}"
             debug=debug+f"\n - validators={NetboxAttachmentValidator.validators}" 
           
        # Loop on the validators to consolidate those that we need to check
        for v in NetboxAttachmentValidator.validators:
            # Consider this one if content type matches
            if instance.object_type_id in v['ctype']:
                # Go further if we are in the allowed groups
                added=False
                for g in v['groups']:
                    if not added :
                        if g in groups:
                            # We should consider this validator
                            vals.append(v)
                            added=True
                        else:
                            if instance.description=="debug":
                                debug=debug+f"\n - group nomatch {g} not in {groups}"  
            else:
                if instance.description=="debug":
                    debug=debug+f"\n - ctype nomatch {instance.object_type_id} not in {v['ctype']}"  
        if instance.description=="debug":
            debug=debug+f"\n - vals={vals}"              
        # Process our validators
        # TODO noter les matchs de files pour alerter sur les formats
        for v in vals:
            if v['file'].match(f"{instance.file}"):
                if v['name'].match(f"{instance.name}"):
                    return

        self.fail(f"Your input didn't match any allowed patterns  : ctype={instance.object_type_id}/file={instance.file}/name={instance.name}"+debug)




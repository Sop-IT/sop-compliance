from extras.validators import CustomValidator
from extras.choices import LogLevelChoices
from ipam.models import IPAddress, Prefix
from sop_infra.utils.sop_utils import CheckResult, CheckResultList, SopRegExps, ValidatorCheckResultLogger
from sop_infra.utils.netbox_utils import NetboxConstants


class IpamRules():

    class RegExps(SopRegExps):
        pass

    @staticmethod
    def check_one_ip_dns_fqdn(ip_address:IPAddress, crl:CheckResultList):
        if ip_address.dns_name is None or ip_address.dns_name.strip()=="":
            return
        if ip_address.status in ['deprecated', 'retired']:
            return
        if not SopRegExps.fqdn_point_re.match(ip_address.dns_name):
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address,f"Invalid dns_name \"{ip_address.dns_name}\" : it must be an FQDN !", "dns_name"))    
    @staticmethod
    def check_ip_dns_fqdn(crl:CheckResultList):
        for ip_address in IPAddress.objects.all():
            IpamRules.check_one_ip_dns_fqdn(ip_address, crl)

    @staticmethod
    def check_one_ip_tenancy(ip_address:IPAddress, crl:CheckResultList):
        if ip_address.tenant is None :
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address, f"{ip_address} : this IP address is missing a valid tenant !", "tenant"))
    @staticmethod
    def check_ips_tenancy(crl:CheckResultList):
        for ip_address in IPAddress.objects.all():
            IpamRules.check_one_ip_tenancy(ip_address, crl)

    @staticmethod
    def check_one_ip_status_consistency(ip_address:IPAddress, crl:CheckResultList):     
        if not hasattr(ip_address.address, "ip"):
            return
        prefixes=Prefix.objects.filter(vrf=ip_address.vrf, prefix__net_contains_or_equals=str(ip_address.address.ip))
        if prefixes is not None and len(prefixes)>0:
            if ip_address.status == "retired": 
                return 
            closet_prefix_parent = prefixes.reverse()[0]
            if closet_prefix_parent.status in ["reserved", "retired"]:
                if ip_address.status != closet_prefix_parent.status :
                    crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address,
                                           f" parent prefix {closet_prefix_parent} is {closet_prefix_parent.status} so this IP must be {closet_prefix_parent.status} also !", "status"))
            elif closet_prefix_parent.status in ["active", "noncompliant", "decommissioning"]:
                if ip_address.address.prefixlen != closet_prefix_parent.prefix.prefixlen:
                    crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address,f"This IP's prefixlen ({ip_address.address.prefixlen}) is inconsistent with parent prefix ({str(closet_prefix_parent.prefix)})"))
            elif closet_prefix_parent.status in ["container"]:
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address,
                                       f" Parent prefix is a container -> ILLEGAL !", "status"))
            else : 
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address,f"Validator logic bug on prefix status \"{closet_prefix_parent.status}\" !", "status"))
            if ip_address.tenant is not None and closet_prefix_parent.tenant is not None and ip_address.tenant.pk!= closet_prefix_parent.tenant.pk:
                crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address,f"This IP's tenant is NOT the same as its parent prefix tenant !", "status"))
        else:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, ip_address,f"This IP is missing a parent prefix !", "status"))
    @staticmethod
    def check_ip_status_consistency(crl:CheckResultList):     
        for ip_address in IPAddress.objects.all():
            IpamRules.check_one_ip_status_consistency(ip_address, crl)


    @staticmethod
    def check_one_prefix_tenancy(prefix:Prefix, crl:CheckResultList):   
        if prefix.status in ["container", 'retired']:
            pass
        elif prefix.tenant is None :
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, prefix, f"{prefix} : this prefix is missing a valid tenant !", "tenant"))
        elif prefix.tenant.id == NetboxConstants.sopit_id:
            pass
        elif prefix.scope is None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, prefix, f"{prefix.tenant.group.name}:{prefix} : this prefix is missing a valid scope !", "scope"))
        elif prefix.scope.tenant is not None and prefix.scope.tenant.id == NetboxConstants.sopit_id:
            pass
        elif prefix.tenant.pk != prefix.scope.tenant.pk:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, prefix, f"{prefix.scope.group.name}:{prefix} : this prefix tenant is not the same as that of its scope {prefix.scope}", "tenant"))    
    @staticmethod
    def check_prefixes_tenancy(crl:CheckResultList):   
        for prefix in Prefix.objects.all():
            IpamRules.check_one_prefix_tenancy(prefix, crl)



# ========================================================================================

class IpAddValidator(CustomValidator):
    def validate(self, instance:IPAddress, request):
        failprefix=f"{instance.address} -> "   
        crl=CheckResultList()
        IpamRules.check_one_ip_dns_fqdn(instance, crl)
        IpamRules.check_one_ip_status_consistency(instance, crl)
        IpamRules.check_one_ip_tenancy(instance, crl)
        crl.dump_to(ValidatorCheckResultLogger(self, failprefix))








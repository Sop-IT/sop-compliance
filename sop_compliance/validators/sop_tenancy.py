import re


from dcim.models import Site
from extras.choices import LogLevelChoices
from extras.validators import CustomValidator
from tenancy.models import Tenant

from sop_infra.utils.sop_utils import CheckResult, CheckResultList, ValidatorCheckResultLogger
from sop_infra.utils.sop_utils import SopRegExps


class ContactRules():

    contact_site_status=['starting', 'active', 'decommissioning']

    @staticmethod
    def check_one_site_mandatory_contacts(site:Site, crl:CheckResultList):
        if site.status not in ContactRules.contact_site_status:
            return
        if site.contacts.filter(role__slug="it", priority="primary").exclude(contact__custom_field_data__ad_acct_disabled=True).count()<=0:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} is missing a valid \"Primary\" \"IT\" contact."))
        if site.contacts.filter(role__slug="telecom", priority="primary").exclude(contact__custom_field_data__ad_acct_disabled=True).count()<=0:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} is missing a valid \"Primary\" \"Telecom\" contact."))
    @staticmethod
    def check_sites_mandatory_contacts(crl:CheckResultList):
        for site in Site.objects.all():
            ContactRules.check_one_site_mandatory_contacts(site, crl)

    @staticmethod
    def check_one_site_wms_contacts(site:Site, crl:CheckResultList):
        # We don't enforce it yet
        return
        if site.status not in ContactRules.contact_site_status:
            return
        # TODO : change to sopinfra before enforcing
        if not site.custom_field_data.get("site_type_wms"):
            return
        if site.contacts.filter(role__slug="wms", priority="primary").exclude(contact__custom_field_data__ad_acct_disabled=True).count()<=0:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} is missing a valid \"Primary\" \"WMS\" contact."))
    @staticmethod
    def check_sites_wms_contacts(crl:CheckResultList):
        for site in Site.objects.all():
            ContactRules.check_one_site_wms_contacts(site, crl)

    @staticmethod
    def check_one_site_indus_contacts(site:Site, crl:CheckResultList):
        # We don't enforce it yet
        return
        if site.status not in ContactRules.contact_site_status:
            return
        # TODO : change to sopinfra before enforcing
        if site.custom_field_data.get("site_type_indus") is None:
            return
        if site.contacts.filter(role__slug="indus", priority="primary").exclude(contact__custom_field_data__ad_acct_disabled=True).count()<=0:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, site, f"{site.group.name}:{site.name} is missing a valid \"Primary\" \"INDUS\" contact."))
    @staticmethod
    def check_sites_indus_contacts(crl:CheckResultList):
        for site in Site.objects.all():
            ContactRules.check_one_site_indus_contacts(site, crl)

    @staticmethod
    def check_one_tenant_billing_contacts(tenant:Tenant, crl:CheckResultList):
        # We don't enforce it yet
        return
        if tenant.custom_field_data.get("obs_ban") is None and tenant.custom_field_data.get("obs_ban_btip") is None:
            return
        if tenant.contacts.filter(role__slug="billing", priority="primary").exclude(contact__custom_field_data__ad_acct_disabled=True).count()<=0:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, tenant, f"{tenant.group.name}:{tenant.name} is missing valid \"Billing\" contact"))
    @staticmethod
    def check_tenants_billing_contacts(crl:CheckResultList):
        for tenant in Tenant.objects.all():
            ContactRules.check_one_tenant_billing_contacts(tenant, crl)

class TenantRules():

    class RegExps():
        tenant_name_str=r'^[^_]+ \('+SopRegExps.iso3166a2_str+r'\)$'
        tenant_name_re=re.compile(tenant_name_str)

    @staticmethod
    def check_one_tenant_billing_master_site (tenant:Tenant, crl:CheckResultList):
        # We don't enforce it yet
        pass
        if tenant.custom_field_data.get("obs_ban") is None and tenant.custom_field_data.get("obs_ban_btip") is None:
            return        
        if tenant.custom_field_data["obs_billing_master_site"] is None:
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, tenant, f"{tenant.group.name}:{tenant.name} : this tenant is missing a billing site."))
        elif Site.objects.filter(pk=tenant.custom_field_data["obs_billing_master_site"], status__in=['retired', 'template', 'inventory', 'teleworker', 'test-poc', 'dc']).first():
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, tenant, f"{tenant.group.name}:{tenant.name} : this tenant's billing site is invalid."))
    @staticmethod
    def check_tenants_billing_master_site (crl:CheckResultList):
        for tenant in Tenant.objects.all():
            TenantRules.check_one_tenant_billing_master_site(tenant, crl)

    @staticmethod
    def check_one_tenant_name(tenant:Tenant, crl:CheckResultList):
        if not TenantRules.RegExps.tenant_name_re.match(tenant.name):
            crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, tenant, f"{tenant.group.name}:{tenant.name} - \
                Invalid tenant name. Expected :  'Full Company Name (XX)' where XX is the ISO3166 ALPHA2 country code.", field='name'))
    @staticmethod
    def check_tenants_names (crl:CheckResultList):
        for tenant in Tenant.objects.all():
            TenantRules.check_one_tenant_name(tenant, crl)

    @staticmethod
    def check_one_tenant_status(tenant:Tenant, crl:CheckResultList):
        pass 
        # plus obligatoire
        #if tenant.cf.get('tenant_status') in ['integration', 'active', 'decommissinning']:
        #    if tenant.cf.get('vat_number') is None or str(tenant.cf.get('vat_number')).strip()=="":
        #        crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, tenant, f"{tenant.group.name}:{tenant.name} - \
        #            tenant with status '{tenant.cf.get('tenant_status')}' requires a VAT NUMBER.", field='cf_vat_number'))
    @staticmethod
    def check_tenants_status (crl:CheckResultList):
        for tenant in Tenant.objects.all():
            TenantRules.check_one_tenant_status(tenant, crl)              

class TenantValidator(CustomValidator):
    def validate(self, instance, request):
        failprefix=f"{instance.slug} -> "
        crl=CheckResultList()
        # Check the tenant name format
        TenantRules.check_one_tenant_name(instance, crl)
        # TODO : cehck duplicates ?
        # Check the integration status ?
        # Check the domain names associated to this tenant
        hasDomains=False
        if  instance.custom_field_data['tenant_nonO365_domain_names'] is not None :
            # TODO : check typeof JSON field
            # Loop on domains
            for dns in instance.custom_field_data['tenant_nonO365_domain_names']:
                # based on https://stackoverflow.com/questions/11809631/fully-qualified-domain-name-validation edit 3
                r=r'(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{0,62}[a-zA-Z0-9]\.)+[a-zA-Z]{2,63}$)'
                if not re.match(r, dns):
                    crl.append(CheckResult(LogLevelChoices.LOG_FAILURE, instance, f"{failprefix}FQDN required -> domains listed must match this regex {r} ", field='cf_tenant_nonO365_domain_names'))
            # Flag has having domains  
            hasDomains=True
        # Domains currently in integration must have domain names
        #if "integration"==instance.custom_field_data['tenant_status']:
        #    if not hasDomains:
        #        self.fail(f"{failprefix}Tenants currently 'in integration' need domains", field='cf_tenant_nonO365_domain_names')
        crl.dump_to(ValidatorCheckResultLogger(self, failprefix))


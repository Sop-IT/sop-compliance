"""
NetBox SopCompliance Plugin

Plugin configuration for NetBox SopCompliance Plugin.

For a complete list of PluginConfig attributes, see:
https://docs.netbox.dev/en/stable/plugins/development/#pluginconfig-attributes
"""

__author__ = """SOPREMA NOC Team"""
__email__ = "noc@soprema.com"
__version__ = "0.1.0"


from netbox.plugins import PluginConfig


class SopcomplianceConfig(PluginConfig):
    name = "sop_compliance"
    verbose_name = "NetBox SopCompliance Plugin"
    description = "Compliance and data validation"
    author= "SOPREMA NOC Team"
    author_email = "noc@soprema.com"
    version = __version__
    base_url = "sop_compliance"
    min_version = "4.5.0"
    max_version = "4.5.99"


config = SopcomplianceConfig

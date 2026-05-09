"""
Navigation menu items for NetBox SopCompliance Plugin.

For more information on navigation menus, see:
https://docs.netbox.dev/en/stable/plugins/development/navigation/
"""

from netbox.plugins import PluginMenuButton, PluginMenuItem

plugin_buttons = [
    PluginMenuButton(
        link="plugins:sop_compliance:sopcompliance_add",
        title="Add",
        icon_class="mdi mdi-plus-thick",
    )
]

menu_items = (
    PluginMenuItem(
        link="plugins:sop_compliance:sopcompliance_list",
        link_text="SopCompliance",
        buttons=plugin_buttons,
    ),
)

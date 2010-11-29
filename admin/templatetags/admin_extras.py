from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa import admin
from modoboa.lib import events, static_url

register = template.Library()

genders = {
    "Enabled" : (_("enabled_m"), _("enabled_f"))
}

@register.simple_tag
def admin_menu(user):
    entries = [
        {"name" : "admin",
         "img" : static_url('pics/admin.png'),
         "label" : _("Admin"),
         "class" : "topdropdown",
         "menu" : []
         }
        ]
    if user.has_perm("admin.view_domains"):
        entries[0]["menu"] += [
            {"name" : "domains",
             "url" : reverse(admin.views.domains),
             "label" : _("Domains"),
             "img" : static_url("pics/domains.png")}
            ]
    elif user.has_perm("admin.view_mailboxes"):
        entries[0]["menu"] += [
            {"name" : "mailboxes",
             "url" : reverse(admin.views.domains),
             "label" : _("Mailboxes"),
             "img" : static_url("pics/mailbox.png")}
            ]
    entries[0]["menu"] += \
        events.raiseQueryEvent("AdminMenuDisplay", target="top_menu", 
                               user=user)
    if user.has_perm("auth.view_permissions"):
        entries[0]["menu"] += [
            {"name" : "permissions",
             "url" : reverse(admin.views.permissions),
             "label" : _("Permissions"),
             "img" : static_url("pics/permissions.png")}
            ]
    if user.is_superuser:
        entries[0]["menu"] += [
            {"name" : "settings",
             "img" : static_url("pics/settings.png"),
             "label" : _("Settings"),
             "url" : reverse(admin.views.viewparameters)}
            ]

    if not len(entries[0]["menu"]):
        return ""
    return render_to_string("common/menulist.html",
                            {"entries" : entries, "user" : user})
        
@register.simple_tag
def domain_menu(domain_id, selection, user):
    entries = [
        {"name" : "",
         "url" : reverse(admin.views.newmailbox, args=[domain_id]),
         "label" : _("New mailbox"),
         "img" : static_url("pics/add.png"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:300,y:280}}"},
        {"name" : "mailboxes",
         "url" : reverse(admin.views.mailboxes, args=[domain_id]),
         "img" : static_url("pics/mailbox.png"),
         "label" : _("Mailboxes")},
        {"name" : "aliases",
         "url" : reverse("full-aliases", args=[domain_id]),
         "img" : static_url("/pics/alias.png"),
         "label" : _("Aliases")},
        ]

    if user.has_perm("admin.change_domain"):
        entries += [
            {"name" : "",
             "url" : reverse(admin.views.editdomain, args=[domain_id]),
             "label" : _("Properties"),
             "img" : static_url("pics/edit.png"),
             "class" : "boxed",
             "rel" : "{handler:'iframe',size:{x:300,y:180}}"}
            ]
    entries += events.raiseQueryEvent("AdminMenuDisplay", target="admin_menu_bar", 
                                      user=user, domain=domain_id)
    return render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries,
                             "user" : user})

@register.simple_tag
def settings_menu(selection, user):
    entries = [
        {"name" : "parameters",
         "url" : reverse(admin.views.viewparameters),
         "img" : static_url("pics/domains.png"),
         "label" : _("Parameters")},
        {"name" : "extensions",
         "url" : reverse(admin.views.viewextensions),
         "label" : _("Extensions"),
         "img" : static_url("pics/extensions.png")},
        ]
    return render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries,
                             "user" : user})

@register.simple_tag
def domains_menu(selection, user):
    entries = [
        {"name" : "newdomain",
         "url" : reverse(admin.views.newdomain),
         "label" : _("New domain"),
         "img" : static_url("pics/add.png"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:300,y:200}}"},
        {"name" : "domains",
         "url" : reverse(admin.views.domains),
         "label" : _("Domains"),
         "img" : static_url("pics/domains.png")}
        ]
    entries += events.raiseQueryEvent("AdminMenuDisplay", target="admin_menu_box",
                                      user=user)
    return render_to_string('common/menu.html', 
                            {"entries" : entries, "selection" : selection,
                             "user" : user})

@register.simple_tag
def permissions_menu(user):
    entries = [
        {"name" : "addperm",
         "label" : _("Add permission"),
         "img" : static_url("pics/add.png"),
         "url" : reverse(admin.views.add_permission)},
        {"name" : "delperms",
         "label" : _("Remove permissions"),
         "img" : static_url("pics/remove.png"),
         "url" : reverse(admin.views.delete_permissions)},
        ]
    return render_to_string('common/menu.html', 
                            {"entries" : entries, "user" : user})

@register.simple_tag
def loadadminextmenu(user):
    menu = events.raiseQueryEvent("AdminMenuDisplay", target="admin_menu_box", 
                                  user=user)
    return render_to_string('common/menulist.html', 
                            {"entries" : menu, "user" : user})

@register.simple_tag
def param(app, definition):
    result = """<div class='row'>
  <label>%s</label>""" % (definition.has_key("label") \
                              and definition["label"] or definition["name"])
    name = "%s.%s" % (app, definition["name"])
    value = definition.has_key("value") \
        and definition["value"] or definition["deflt"]

    if definition["type"] in ["string", "int"]:
        result += """
  <input type='text' name='%s' id='%s' value='%s' />""" % (name, name, value)

    if definition["type"] == "text":
        result += "<textarea name='%s' id='%s'>%s</textarea>" \
            % (name, name, value)

    if definition["type"] in ["list", "list_yesno"]:
        result += """
<select name='%s' id='%s'>""" % (name, name)
        values = []
        if definition["type"] == "list_yesno":
            values = [("yes", _("Yes")), ("no", _("No"))]
        else:
            if definition.has_key("values"):
                values = definition["values"]
        for v in values:
            selected = ""
            if value == v[0]:
                selected = " selected='selected'"
            result += "<option value='%s'%s>%s</option>\n" % (v[0], selected, v[1])
        result += """
</select>
"""

    if definition.has_key("help"):
        result += """
  <a href='%s' onclick='return false;' class='Tips' title='%s'>
    <img src='%s' border='0' />
  </a>""" % (definition["help"], _("Help"), static_url("pics/info.png"))
    result += """
</div>
"""
    return result

@register.filter
def gender(value, target):
    if genders.has_key(value):
        return target == "m" and genders[value][0] or genders[value][1]
    return value

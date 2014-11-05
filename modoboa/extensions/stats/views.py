# coding: utf-8
import re
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import (
    login_required, user_passes_test, permission_required
)

from modoboa.core.extensions import exts_pool
from modoboa.lib import events
from modoboa.lib.exceptions import BadRequest, PermDeniedException, NotFound
from modoboa.lib.webutils import (
    _render_to_string, render_to_json_response
)
from modoboa.extensions.admin.models import (
    Domain
)
from modoboa.extensions.stats.grapher import periods, str2Time, Grapher


@login_required
@permission_required("admin.view_mailboxes")
def index(request):
    """
    FIXME: how to select a default graph set ?
    """
    deflocation = "graphs/?gset=mailtraffic"
    if not request.user.is_superuser:
        if not Domain.objects.get_for_admin(request.user).count():
            raise NotFound(_("No statistics available"))

    period = request.GET.get("period", "day")
    graph_sets = events.raiseDictEvent('GetGraphSets')
    return render(request, 'stats/index.html', {
        "periods": periods,
        "period": period,
        "selection": "stats",
        "deflocation": deflocation,
        "graph_sets": graph_sets
    })


def check_domain_access(user, pattern):
    """Check if an administrator can access a domain/relay domain.

    If a non super administrator asks for the global view, we give him
    a view on the first domain he manage instead.

    :return: a domain name (str) or None.
    """
    targets = [Domain]
    if exts_pool.is_extension_enabled("postfix_relay_domains"):
        from modoboa.extensions.postfix_relay_domains.models import RelayDomain
        targets.append(RelayDomain)

    if pattern in [None, "global"]:
        if not user.is_superuser:
            for target in targets:
                if not target.objects.get_for_admin(user).count():
                    continue
                return target.objects.get_for_admin(user)[0].name
            return None
        return "global"

    for target in targets:
        results = target.objects.filter(name__contains=pattern)
        if results.count() != 1:
            continue
        if not user.can_access(results[0]):
            raise PermDeniedException
        return results[0].name
    return None


@login_required
@user_passes_test(lambda u: u.group != "SimpleUsers")
def graphs(request):
    gset = request.GET.get("gset", None)
    gsets = events.raiseDictEvent("GetGraphSets")
    if not gset in gsets:
        raise NotFound(_("Unknown graphic set"))
    searchq = request.GET.get("searchquery", None)
    period = request.GET.get("period", "day")
    tplvars = dict(graphs=[], period=period)
    domain = check_domain_access(request.user, searchq)
    if domain is None:
        return render_to_json_response({})
    tplvars["domain"] = domain

    if period == "custom":
        if not "start" in request.GET or not "end" in request.GET:
            raise BadRequest(_("Bad custom period"))
        start = request.GET["start"]
        end = request.GET["end"]
        G = Grapher()
        expr = re.compile(r'[:\- ]')
        period_name = "%s_%s" % (expr.sub('', start), expr.sub('', end))
        for tpl in gsets[gset].get_graphs():
            tplvars['graphs'].append(tpl.display_name)
            G.process(
                tplvars["domain"], period_name, str2Time(*expr.split(start)),
                str2Time(*expr.split(end)), tpl
            )
        tplvars["period_name"] = period_name
        tplvars["start"] = start
        tplvars["end"] = end
    else:
        tplvars['graphs'] = gsets[gset].get_graph_names()

    return render_to_json_response({
        'content': _render_to_string(request, "stats/graphs.html", tplvars)
    })


@login_required
@user_passes_test(lambda u: u.group != "SimpleUsers")
def get_domain_list(request):
    """Get the list of domains (and relay domains) the user can see."""
    doms = [dom.name for dom in Domain.objects.get_for_admin(request.user)]
    if exts_pool.is_extension_enabled("postfix_relay_domains"):
        from modoboa.extensions.postfix_relay_domains.models import RelayDomain
        doms += [
            rdom.name for rdom in
            RelayDomain.objects.get_for_admin(request.user)
        ]
    return render_to_json_response(doms)

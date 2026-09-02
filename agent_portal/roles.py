"""
Which "portal" a logged-in user lands on.

Phase 1 only really built out the Agent experience (see AgentProfile). This
adds Analyst and Director as real, distinct logins — each with its own
lightweight landing page — without pretending they're full features yet.
Role is intentionally NOT something the login page's tab selector decides;
it's determined here, from the actual account, so a mismatched tab click
(e.g. an Agent account clicking the "Director" tab) can't fake its way into
a portal it doesn't belong to. It just lands the person on their real one.

Analyst/Director aren't separate models — there's no per-user data to hang
off them yet (unlike AgentProfile, which carries region/avatar/streak/etc.),
so plain Django auth Groups are enough to mark "this account is that role."
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

ROLE_AGENT = "agent"
ROLE_ANALYST = "analyst"
ROLE_DIRECTOR = "director"

GROUP_ANALYST = "Incentive Analyst"
GROUP_DIRECTOR = "Director"

ROLE_LABELS = {
    ROLE_AGENT: "Field Agent",
    ROLE_ANALYST: "Incentive Analyst",
    ROLE_DIRECTOR: "Director",
}


def get_user_role(user):
    """The account's real role, checked in a fixed priority order. An
    AgentProfile wins first (that's the fully-built experience); group
    membership covers Analyst/Director; a superuser with neither is treated
    as a Director so `createsuperuser` alone is enough to explore that
    portal without also needing to assign a group by hand."""
    if not user.is_authenticated:
        return None
    if hasattr(user, "agent_profile"):
        return ROLE_AGENT
    if user.groups.filter(name=GROUP_DIRECTOR).exists():
        return ROLE_DIRECTOR
    if user.groups.filter(name=GROUP_ANALYST).exists():
        return ROLE_ANALYST
    if user.is_superuser:
        return ROLE_DIRECTOR
    return None


def url_name_for_role(role):
    return {
        ROLE_AGENT: "dashboard",
        ROLE_ANALYST: "analyst_dashboard",
        ROLE_DIRECTOR: "director_dashboard",
    }.get(role)


def redirect_to_own_portal(user):
    """Send someone to whichever portal their actual role owns. Falls back
    to the login page's 'no role assigned yet' explanation for an account
    that isn't an Agent, isn't in either group, and isn't a superuser —
    should only ever happen for a bare `manage.py createsuperuser`-free
    account created by hand without a role attached."""
    role = get_user_role(user)
    url_name = url_name_for_role(role)
    if url_name:
        return redirect(url_name)
    return redirect("no_role")


def role_required(*allowed_roles):
    """Like @login_required, but also gates on role. A logged-in user
    hitting a portal that isn't theirs is bounced to their OWN portal
    rather than shown an error — typing '/director/' as an Agent isn't
    something to punish, just redirect past."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            role = get_user_role(request.user)
            if role not in allowed_roles:
                return redirect_to_own_portal(request.user)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator

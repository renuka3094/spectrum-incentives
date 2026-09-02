from . import roles

# The topbar's avatar chip normally shows AgentProfile.avatar_emoji — but
# Analyst/Director accounts have no AgentProfile at all (see roles.py), so
# without a fallback that chip would render an empty circle for them. Reuses
# the same emoji as each role's login-page tab, so the identity is visually
# consistent from the login screen through to every page after it.
ROLE_FALLBACK_EMOJI = {
    roles.ROLE_ANALYST: "📊",
    roles.ROLE_DIRECTOR: "🧭",
}


def topbar_avatar(request):
    """Adds `topbar_fallback_emoji` to every template's context — only
    meaningful (and only used, see base.html) for a logged-in user with no
    agent_profile. Cheap: no DB query beyond what request.user already is."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or hasattr(user, "agent_profile"):
        return {}
    role = roles.get_user_role(user)
    return {
        "topbar_fallback_emoji": ROLE_FALLBACK_EMOJI.get(role, "👤"),
        "topbar_role_label": roles.ROLE_LABELS.get(role, ""),
    }

import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import insights
from . import roles
from .models import AgentProfile, Product, Incentive, Sale


def _get_agent_or_none(request):
    return getattr(request.user, "agent_profile", None)


class SpectrumLoginView(LoginView):
    """Same as Django's built-in LoginView, but hands the template a live
    'here's what's happening' teaser so the login screen sells the incentive
    before anyone's even signed in, and — since one login form now serves
    three account types (Agent / Incentive Analyst / Director, picked via
    tabs that are purely presentational, see login.html) — routes a
    successful login to whichever portal the *account itself* actually
    belongs to, not whichever tab was showing when the form was submitted."""

    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["teaser"] = insights.public_teaser()
        return context

    def get_success_url(self):
        role = roles.get_user_role(self.request.user)
        url_name = roles.url_name_for_role(role)
        if url_name:
            return reverse(url_name)
        return super().get_success_url()


@login_required
def dashboard(request):
    agent = _get_agent_or_none(request)
    if agent is None:
        # Not every logged-in account is an Agent anymore — an Analyst or
        # Director hitting "/" directly (a bookmark, a stale link) should
        # land on their own portal, not see "no profile" as if something's
        # broken.
        role = roles.get_user_role(request.user)
        if role in (roles.ROLE_ANALYST, roles.ROLE_DIRECTOR):
            return roles.redirect_to_own_portal(request.user)
        return render(request, "agent_portal/no_profile.html")

    incentive = insights.get_active_incentive()

    # Every sync_* call here does two jobs at once: it persists anything the
    # agent newly qualifies for (a login-streak badge, a quest, a mystery
    # box), AND hands back exactly what was newly earned *this call* — which
    # is empty almost every time, except the first page load after whatever
    # tipped it over. Since sales now start "pending" and only count once an
    # admin approves them (see Sale.status), that tipping point is often a
    # page load, not the log-sale click itself — an approval can land while
    # the agent is away, so the celebratory toast/mystery-box needs to be
    # able to fire on *this* load, not just right after a POST. Crucially,
    # this all has to run BEFORE build_dashboard_context() below, since that
    # computes lifetime_points/lifetime_cash — otherwise a badge/quest/box
    # synced by this exact request wouldn't show up in its own points total.
    new_achievements = insights.sync_achievements(agent)
    new_tasks = insights.sync_bonus_tasks(agent, incentive)
    new_mystery_boxes = insights.sync_goal_bonuses(agent, incentive)

    context = insights.build_dashboard_context(agent)
    context["agent"] = agent
    context["products"] = Product.objects.filter(is_active=True).select_related("category")

    achievements = insights.achievements_context(agent)
    context["achievements"] = achievements
    context["achievements_earned_count"] = sum(1 for a in achievements if a["earned"])
    context["achievements_total_count"] = len(achievements)

    context["leaderboard_region"] = insights.leaderboard_rows(agent, incentive, scope="region")
    context["leaderboard_company"] = insights.leaderboard_rows(agent, incentive, scope="company")
    context["pace"] = insights.pace_comparison(agent)
    context["avatar_choices"] = insights.AVATAR_CHOICES

    tasks = insights.bonus_tasks_context(agent, incentive)
    context["tasks"] = tasks
    context["tasks_done_count"] = sum(1 for t in tasks if t["done"])
    context["tasks_total_count"] = len(tasks)
    context["bonus_points_current"] = insights.bonus_points_current(agent, incentive)
    context["rewards"] = insights.reward_catalog(agent, incentive)

    context["recent_sales"] = insights.recent_sales_for_agent(agent)
    context["daily_log_cap"] = insights.DAILY_LOG_QUANTITY_CAP
    context["daily_logged"] = insights.daily_logged_quantity(agent)
    context["daily_remaining"] = max(0, insights.DAILY_LOG_QUANTITY_CAP - context["daily_logged"])

    history = (
        Sale.objects.approved()
        .filter(agent=agent)
        .values("incentive__name", "incentive__period_start")
        .annotate(points=Sum("points_earned"))
        .order_by("incentive__period_start")
    )
    context["history_json"] = json.dumps(
        [
            {"label": h["incentive__period_start"].strftime("%b"), "points": h["points"]}
            for h in history
        ]
    )
    context["period_end_json"] = json.dumps(incentive.period_end.isoformat() if incentive else None)
    context["agent_name_json"] = json.dumps(agent.display_name)
    context["agent_avatar_json"] = json.dumps(agent.avatar_emoji)
    context["new_achievements_json"] = json.dumps(
        [{"key": a["key"], "name": a["name"], "emoji": a["emoji"]} for a in new_achievements]
    )
    context["new_tasks_json"] = json.dumps(
        [{"key": t["key"], "name": t["name"], "emoji": t["emoji"], "points": t["points"]} for t in new_tasks]
    )
    context["new_mystery_boxes_json"] = json.dumps(new_mystery_boxes)
    return render(request, "agent_portal/dashboard.html", context)


@login_required
@require_POST
def api_log_sale(request):
    """Records a self-reported sale — but, unlike every other number in this
    app, a sale you log yourself does NOT immediately count toward your
    points, tier, goals, badges, or quests. It's saved as 'pending' and only
    starts counting once an admin approves it (Sale admin → select rows →
    'Approve selected sales'; a stand-in for the not-yet-built Director
    approval queue). That's the honest trade-off of letting a real reward
    system trust a self-reported number at all — see the README for the
    reasoning. A daily quantity cap limits how many attempts one agent can
    submit in a day, approved or not."""
    agent = _get_agent_or_none(request)
    if agent is None:
        return HttpResponseBadRequest("No agent profile.")

    try:
        payload = json.loads(request.body or "{}")
        product_id = int(payload["product_id"])
        quantity = max(1, int(payload.get("quantity", 1)))
    except (KeyError, ValueError, TypeError):
        return HttpResponseBadRequest("Malformed request.")

    incentive = insights.get_active_incentive()
    if incentive is None:
        return JsonResponse({"error": "No active incentive right now."}, status=400)

    product = Product.objects.filter(id=product_id, is_active=True).first()
    if product is None:
        return JsonResponse({"error": "Unknown product."}, status=400)

    already_today = insights.daily_logged_quantity(agent)
    if already_today + quantity > insights.DAILY_LOG_QUANTITY_CAP:
        remaining = max(0, insights.DAILY_LOG_QUANTITY_CAP - already_today)
        return JsonResponse(
            {
                "error": (
                    f"Daily logging cap reached ({insights.DAILY_LOG_QUANTITY_CAP} units/day). "
                    f"You have {remaining} left today."
                )
            },
            status=400,
        )

    Sale.objects.create(
        agent=agent,
        product=product,
        incentive=incentive,
        quantity=quantity,
        points_earned=0,
        status=Sale.STATUS_PENDING,
    )

    daily_logged = insights.daily_logged_quantity(agent)
    recent_sales_html = render_to_string(
        "agent_portal/_recent_sales.html",
        {"recent_sales": insights.recent_sales_for_agent(agent)},
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "status": "pending",
            "daily_logged": daily_logged,
            "daily_remaining": max(0, insights.DAILY_LOG_QUANTITY_CAP - daily_logged),
            "recent_sales_html": recent_sales_html,
        }
    )


@login_required
def api_insights(request):
    """Lets the dashboard 'refresh AI insights' without a full page reload."""
    agent = _get_agent_or_none(request)
    if agent is None:
        return HttpResponseBadRequest("No agent profile.")

    incentive = insights.get_active_incentive()
    trending = insights.nearby_trending(agent, incentive)
    tip = insights.fastest_path_tip(agent, incentive)
    mo = insights.momentum(agent, incentive)

    return JsonResponse(
        {
            "trending": trending,
            "tip": (
                {
                    "product": tip["product"].name,
                    "units_needed": tip["units_needed"],
                }
                if tip
                else None
            ),
            "momentum": mo,
        }
    )


@login_required
def api_activity(request):
    """Powers the live company-wide activity ticker without a full page
    reload — polled every so often by the dashboard's JS."""
    return JsonResponse({"items": insights.recent_activity_feed()})


@login_required
@require_POST
def api_set_avatar(request):
    """Lets an agent pick their own emoji avatar from the fixed AVATAR_CHOICES list."""
    agent = _get_agent_or_none(request)
    if agent is None:
        return HttpResponseBadRequest("No agent profile.")

    try:
        payload = json.loads(request.body or "{}")
        avatar = payload["avatar"]
    except (KeyError, ValueError, TypeError):
        return HttpResponseBadRequest("Malformed request.")

    if avatar not in insights.AVATAR_CHOICES:
        return JsonResponse({"error": "Not a valid avatar choice."}, status=400)

    agent.avatar_emoji = avatar
    agent.save(update_fields=["avatar_emoji"])
    return JsonResponse({"ok": True, "avatar": avatar})


@roles.role_required(roles.ROLE_ANALYST, roles.ROLE_DIRECTOR)
def analyst_dashboard(request):
    """Minimal, real (not mocked) Incentive Analyst landing page — see
    insights.analyst_overview() and the module docstring above it for what
    'minimal' means here. A Director can see this too, since a Director
    account is also allowed to answer 'is the program healthy right now'
    without needing a separate Analyst login."""
    return render(request, "agent_portal/analyst_dashboard.html", {"overview": insights.analyst_overview()})


@roles.role_required(roles.ROLE_DIRECTOR)
def director_dashboard(request):
    """Minimal, real Director landing page — see insights.director_overview()."""
    return render(request, "agent_portal/director_dashboard.html", {"overview": insights.director_overview()})


@login_required
def no_role(request):
    """Reached only by a logged-in account that isn't an Agent, isn't in
    either the Analyst or Director group, and isn't a superuser — i.e. an
    account created by hand without being assigned anywhere. Not something
    the seeded demo data ever produces; here as a friendly dead end rather
    than a 500 if it ever does happen."""
    return render(request, "agent_portal/no_role.html")

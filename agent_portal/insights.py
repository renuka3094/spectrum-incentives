"""
Rule-based "AI" insight engine.

No external model or API call — everything here is plain Python reasoning over
the sales data already in the database. It is written to *read* like an AI
assistant (it explains its "why"), which keeps the whole app dependency-free,
offline-friendly, and free to run.
"""

import random
from datetime import timedelta

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import (
    Incentive, IncentiveTierRule, IncentiveProductGoal, Product, Sale, Tier, AgentAchievement, AgentProfile,
    AgentTaskCompletion, AgentGoalBonus,
)

# Emoji options for the avatar picker. Kept as a plain list (not a model) —
# same reasoning as the achievement catalog: this is a fixed product choice,
# not something anyone needs to edit at runtime.
AVATAR_CHOICES = [
    "🚀", "⚡", "🌟", "🔥", "🎯", "🧠", "🐺", "🦊",
    "🐯", "🦁", "🐸", "🐙", "🌊", "🍀", "🎮", "👾",
    "🛹", "🥷", "🎧", "🏄",
]


def get_active_incentive():
    today = timezone.localdate()
    return (
        Incentive.objects.filter(is_active=True, period_start__lte=today, period_end__gte=today)
        .order_by("-period_start")
        .first()
    )


def agent_points(agent, incentive):
    if not incentive:
        return 0
    total = Sale.objects.approved().filter(agent=agent, incentive=incentive).aggregate(total=Sum("points_earned"))["total"]
    return total or 0


def tier_progress(agent, incentive):
    """Where the agent stands on the Silver → Gold → Diamond ladder for this incentive."""
    if not incentive:
        return None

    rules = list(
        IncentiveTierRule.objects.filter(incentive=incentive).select_related("tier").order_by("tier__order")
    )
    if not rules:
        return None

    points = agent_points(agent, incentive)

    current_rule = None
    next_rule = None
    for rule in rules:
        if points >= rule.points_required:
            current_rule = rule
        elif next_rule is None:
            next_rule = rule

    if next_rule:
        span = next_rule.points_required - (current_rule.points_required if current_rule else 0)
        earned_in_span = points - (current_rule.points_required if current_rule else 0)
        pct = max(0, min(100, round((earned_in_span / span) * 100))) if span else 100
        points_to_next = max(0, next_rule.points_required - points)
    else:
        pct = 100
        points_to_next = 0

    return {
        "points": points,
        "current_tier": current_rule.tier if current_rule else None,
        "next_tier": next_rule.tier if next_rule else None,
        "next_tier_points": next_rule.points_required if next_rule else None,
        "points_to_next": points_to_next,
        "pct_to_next": pct,
        "is_maxed": next_rule is None,
        "all_tiers": [
            {
                "tier": r.tier,
                "points_required": r.points_required,
                "reached": points >= r.points_required,
            }
            for r in rules
        ],
    }


def product_goal_progress(agent, incentive):
    """Per-product sell-through: target vs. what this agent has actually sold."""
    if not incentive:
        return []

    goals = IncentiveProductGoal.objects.filter(incentive=incentive).select_related("product", "product__category")
    sold_by_product = dict(
        Sale.objects.approved().filter(agent=agent, incentive=incentive)
        .values("product_id")
        .annotate(qty=Sum("quantity"))
        .values_list("product_id", "qty")
    )

    rows = []
    for goal in goals:
        sold = sold_by_product.get(goal.product_id, 0)
        pct = max(0, min(100, round((sold / goal.target_quantity) * 100))) if goal.target_quantity else 0
        rows.append(
            {
                "product": goal.product,
                "target": goal.target_quantity,
                "sold": sold,
                "remaining": max(0, goal.target_quantity - sold),
                "pct": pct,
                "points_per_unit": goal.points_per_unit,
                "complete": sold >= goal.target_quantity,
            }
        )
    rows.sort(key=lambda r: (r["complete"], -r["pct"]))
    return rows


def product_points_map(incentive):
    """product_id -> points-per-unit for every active product, honoring a
    per-incentive points_override where one exists (see
    IncentiveProductGoal.points_per_unit) and falling back to the product's
    own base_points otherwise. Powers the Log a Sale modal's live
    point-impact preview client-side — computed once here, server-side, so
    the 'how many points is this worth' rule lives in exactly one place
    rather than being re-implemented in JS."""
    overrides = {}
    if incentive:
        overrides = dict(
            IncentiveProductGoal.objects.filter(incentive=incentive).values_list(
                "product_id", "points_override"
            )
        )
    return {
        p.id: overrides.get(p.id) or p.base_points
        for p in Product.objects.filter(is_active=True)
    }


def nearby_trending(agent, incentive, limit=3):
    """
    'What are people near me buying?' — looks at every sale logged this incentive
    period by agents in the SAME region, ranks products by momentum, and flags
    the ones this agent personally hasn't leaned into yet.
    """
    if not incentive or not agent.region_id:
        return []

    region_sales = (
        Sale.objects.approved().filter(incentive=incentive, agent__region_id=agent.region_id)
        .values("product__name", "product_id", "product__category__name")
        .annotate(region_units=Sum("quantity"), region_agents=Count("agent", distinct=True))
        .order_by("-region_units")
    )

    my_units = dict(
        Sale.objects.approved().filter(agent=agent, incentive=incentive)
        .values("product_id")
        .annotate(qty=Sum("quantity"))
        .values_list("product_id", "qty")
    )

    insights = []
    for row in region_sales:
        my_qty = my_units.get(row["product_id"], 0)
        if row["region_units"] < 2:
            continue
        gap_score = row["region_units"] - my_qty
        insights.append(
            {
                "product_name": row["product__name"],
                "category": row["product__category__name"],
                "region_units": row["region_units"],
                "region_agents": row["region_agents"],
                "my_units": my_qty,
                "gap_score": gap_score,
            }
        )

    insights.sort(key=lambda r: r["gap_score"], reverse=True)
    return insights[:limit]


def fastest_path_tip(agent, incentive):
    """Which single product gets this agent to the next tier in the fewest units?"""
    progress = tier_progress(agent, incentive)
    if not progress or progress["is_maxed"] or not progress["points_to_next"]:
        return None

    goals = IncentiveProductGoal.objects.filter(incentive=incentive).select_related("product")
    if not goals:
        return None

    best = None
    for goal in goals:
        per_unit = goal.points_per_unit or 1
        units_needed = -(-progress["points_to_next"] // per_unit)  # ceil division
        if best is None or units_needed < best["units_needed"]:
            best = {"product": goal.product, "units_needed": units_needed, "per_unit": per_unit}
    return best


def momentum(agent, incentive):
    """Simple week-over-week trend: are this agent's points accelerating?"""
    if not incentive:
        return None
    now = timezone.now()
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)

    this_week = (
        Sale.objects.approved().filter(agent=agent, incentive=incentive, sold_at__gte=this_week_start).aggregate(
            total=Sum("points_earned")
        )["total"]
        or 0
    )
    last_week = (
        Sale.objects.approved().filter(
            agent=agent, incentive=incentive, sold_at__gte=last_week_start, sold_at__lt=this_week_start
        ).aggregate(total=Sum("points_earned"))["total"]
        or 0
    )

    if last_week == 0:
        trend = "up" if this_week > 0 else "flat"
        delta_pct = None
    else:
        delta_pct = round(((this_week - last_week) / last_week) * 100)
        trend = "up" if delta_pct > 5 else ("down" if delta_pct < -5 else "flat")

    return {"this_week": this_week, "last_week": last_week, "trend": trend, "delta_pct": delta_pct}


def lifetime_points(agent):
    """All-time points across every incentive this agent has ever run —
    logged sales, every bonus quest they've banked, and every mystery-box
    surprise they've popped. This is the 'total points achieved' headline
    stat: unlike the tier ring (which only counts the *current* incentive),
    this never resets."""
    sale_total = Sale.objects.approved().filter(agent=agent).aggregate(t=Sum("points_earned"))["t"] or 0
    bonus_total = AgentTaskCompletion.objects.filter(agent=agent).aggregate(t=Sum("points_awarded"))["t"] or 0
    mystery_total = AgentGoalBonus.objects.filter(agent=agent).aggregate(t=Sum("points_awarded"))["t"] or 0
    return sale_total + bonus_total + mystery_total


# Placeholder $/point payout rate — there's no real commission dollar figure
# anywhere in this demo's data, so lifetime points are converted at this fixed
# rate to give a "total cash earned" headline number. Swap this (or replace
# total_cash_earned() with a real per-sale dollar model) once actual payout
# numbers are available.
CASH_PER_POINT = 0.75


def total_cash_earned(agent):
    """Lifetime points converted to an approximate cash value, rounded to the
    nearest whole dollar for a clean stat-tile count-up."""
    return round(lifetime_points(agent) * CASH_PER_POINT)


# Max units a single agent can self-log in one calendar day, across every
# product and regardless of whether a given submission ends up approved or
# rejected — a self-reported number that feeds rewards has to have *some*
# ceiling, or an agent could just keep clicking "Log a sale" forever. This
# doesn't replace real verification (see Sale.status/SaleQuerySet.approved) —
# it just bounds how many attempts a day can produce.
DAILY_LOG_QUANTITY_CAP = 15


def daily_logged_quantity(agent, day=None):
    """Units this agent has already self-logged today, any status — what the
    daily cap is checked against."""
    day = day or timezone.localdate()
    return Sale.objects.filter(agent=agent, sold_at__date=day).aggregate(t=Sum("quantity"))["t"] or 0


def recent_sales_for_agent(agent, limit=6):
    """The agent's own most recent submissions, every status included — this
    is the transparency/audit view: 'here's exactly what I logged and where
    it stands,' shown right in the log-sale modal so it never costs extra
    scrolling on the main page."""
    sales = Sale.objects.filter(agent=agent).select_related("product").order_by("-sold_at")[:limit]
    return [
        {
            "id": s.id,
            "product": s.product.name,
            "quantity": s.quantity,
            "points": s.points_earned,
            "status": s.status,
            "status_label": s.get_status_display(),
            "sold_at": s.sold_at,
        }
        for s in sales
    ]


def recent_activity_feed(limit=12):
    """A live, company-wide 'what's happening right now' feed — the most
    recent sales and freshly-unlocked badges across every region, not just
    the viewer's own. Plain descriptive strings, cheap enough to poll often
    for the scrolling ticker."""
    incentive = get_active_incentive()
    if not incentive:
        return []

    items = []
    recent_sales = (
        Sale.objects.approved().filter(incentive=incentive)
        .select_related("agent__user", "product")
        .order_by("-sold_at")[: limit * 2]
    )
    for sale in recent_sales:
        items.append(
            {
                "ts": sale.sold_at,
                "text": f"{sale.agent.avatar_emoji} {sale.agent.display_name} sold {sale.quantity}x {sale.product.name}",
            }
        )

    achievement_names = {a["key"]: a["name"] for a in ACHIEVEMENTS}
    recent_achievements = (
        AgentAchievement.objects.select_related("agent__user").order_by("-earned_at")[:limit]
    )
    for ach in recent_achievements:
        items.append(
            {
                "ts": ach.earned_at,
                "text": f"🏅 {ach.agent.avatar_emoji} {ach.agent.display_name} unlocked {achievement_names.get(ach.key, ach.key)}",
            }
        )

    items.sort(key=lambda i: i["ts"], reverse=True)
    return [i["text"] for i in items[:limit]]


def build_dashboard_context(agent):
    incentive = get_active_incentive()
    goals = product_goal_progress(agent, incentive)
    return {
        "incentive": incentive,
        "progress": tier_progress(agent, incentive),
        "goals": goals,
        "units_remaining": sum(g["remaining"] for g in goals),
        "trending": nearby_trending(agent, incentive),
        "tip": fastest_path_tip(agent, incentive),
        "momentum": momentum(agent, incentive),
        "lifetime_points": lifetime_points(agent),
        "lifetime_cash": total_cash_earned(agent),
        "activity_feed": recent_activity_feed(),
    }


# ---------------------------------------------------------------------------
# Achievements — a fixed badge catalog defined in code (not a DB-editable
# model, since the badge set is a product decision, not something an analyst
# configures). Each entry's `check(agent)` is plain Python/ORM logic; nothing
# here calls an external service.
# ---------------------------------------------------------------------------


def _agent_incentives(agent):
    """Every incentive this agent has ever logged a sale against."""
    return Incentive.objects.filter(sales__agent=agent).distinct()


def _check_first_sale(agent):
    return Sale.objects.approved().filter(agent=agent).exists()


def _check_fast_starter(agent):
    for sale in Sale.objects.approved().filter(agent=agent).select_related("incentive"):
        if sale.sold_at.date() <= sale.incentive.period_start + timedelta(days=2):
            return True
    return False


def _check_category_crusher(agent):
    for incentive in _agent_incentives(agent):
        if any(g["complete"] for g in product_goal_progress(agent, incentive)):
            return True
    return False


def _check_diamond_elite(agent):
    for incentive in _agent_incentives(agent):
        progress = tier_progress(agent, incentive)
        if progress and progress["current_tier"] and progress["current_tier"].order >= 3:
            return True
    return False


def _check_century_club(agent):
    return (
        Sale.objects.approved().filter(agent=agent)
        .annotate(day=TruncDate("sold_at"))
        .values("day")
        .annotate(total=Sum("points_earned"))
        .filter(total__gte=100)
        .exists()
    )


def _check_consistency_star(agent):
    incentive = get_active_incentive()
    if not incentive:
        return False
    weeks = {
        sold_at.isocalendar()[1]
        for sold_at in Sale.objects.approved().filter(agent=agent, incentive=incentive).values_list("sold_at", flat=True)
    }
    return len(weeks) >= 3


def _check_team_mvp(agent):
    incentive = get_active_incentive()
    if not incentive or not agent.region_id:
        return False
    ranking = list(
        Sale.objects.approved().filter(incentive=incentive, agent__region_id=agent.region_id)
        .values("agent")
        .annotate(total=Sum("points_earned"))
        .order_by("-total")
    )
    return len(ranking) >= 2 and ranking[0]["agent"] == agent.id and ranking[0]["total"] > 0


def _check_streak_starter(agent):
    return agent.longest_login_streak >= 3


def _check_streak_legend(agent):
    return agent.longest_login_streak >= 7


ACHIEVEMENTS = [
    {
        "key": "first_sale",
        "name": "First Blood",
        "emoji": "🏁",
        "description": "Log your very first sale.",
        "check": _check_first_sale,
    },
    {
        "key": "fast_starter",
        "name": "Fast Starter",
        "emoji": "🚀",
        "description": "Log a sale within the first 3 days of an incentive period.",
        "check": _check_fast_starter,
    },
    {
        "key": "category_crusher",
        "name": "Category Crusher",
        "emoji": "🎯",
        "description": "Hit 100% of the target on any single product goal.",
        "check": _check_category_crusher,
    },
    {
        "key": "century_club",
        "name": "Century Club",
        "emoji": "💯",
        "description": "Earn 100+ points in a single day.",
        "check": _check_century_club,
    },
    {
        "key": "consistency_star",
        "name": "Consistency Star",
        "emoji": "⭐",
        "description": "Log a sale in 3 different weeks of the same incentive.",
        "check": _check_consistency_star,
    },
    {
        "key": "team_mvp",
        "name": "Team MVP",
        "emoji": "🏆",
        "description": "Be the top scorer in your region for the current incentive.",
        "check": _check_team_mvp,
    },
    {
        "key": "diamond_elite",
        "name": "Diamond Elite",
        "emoji": "💎",
        "description": "Reach Diamond tier in any incentive.",
        "check": _check_diamond_elite,
    },
    {
        "key": "streak_starter",
        "name": "Streak Starter",
        "emoji": "🔆",
        "description": "Log in 3 days in a row.",
        "check": _check_streak_starter,
    },
    {
        "key": "streak_legend",
        "name": "Streak Legend",
        "emoji": "🌟",
        "description": "Log in 7 days in a row.",
        "check": _check_streak_legend,
    },
]


def sync_achievements(agent):
    """Persist any badges the agent newly qualifies for. Returns the list of
    catalog entries (dicts, minus the `check` callable) earned *this call* —
    empty most of the time, non-empty right after the action that tipped it
    over (a sale, a login streak update)."""
    already = set(AgentAchievement.objects.filter(agent=agent).values_list("key", flat=True))
    newly_earned = []
    for ach in ACHIEVEMENTS:
        if ach["key"] in already:
            continue
        if ach["check"](agent):
            AgentAchievement.objects.get_or_create(agent=agent, key=ach["key"])
            newly_earned.append({k: v for k, v in ach.items() if k != "check"})
    return newly_earned


def achievements_context(agent):
    """The full badge shelf — locked and unlocked — for rendering."""
    earned = {
        row["key"]: row["earned_at"]
        for row in AgentAchievement.objects.filter(agent=agent).values("key", "earned_at")
    }
    return [
        {
            "key": ach["key"],
            "name": ach["name"],
            "emoji": ach["emoji"],
            "description": ach["description"],
            "earned": ach["key"] in earned,
            "earned_at": earned.get(ach["key"]),
        }
        for ach in ACHIEVEMENTS
    ]


# ---------------------------------------------------------------------------
# Bonus quests ("Available Tasks") — a fixed, bite-sized checklist that sits
# alongside the big per-product Goals. Same fixed-catalog-in-code pattern as
# ACHIEVEMENTS, except quests are scoped to one incentive period (they reset
# every month) instead of being permanent, so each check function takes the
# incentive too and completions are stored per (agent, incentive, key).
# ---------------------------------------------------------------------------


def _task_check_quick_starter(agent, incentive):
    cutoff = incentive.period_start + timedelta(days=3)
    return Sale.objects.approved().filter(agent=agent, incentive=incentive, sold_at__date__lte=cutoff).exists()


def _task_check_category_explorer(agent, incentive):
    cats = set(
        Sale.objects.approved().filter(agent=agent, incentive=incentive).values_list("product__category_id", flat=True)
    )
    return len(cats) >= 2


def _task_check_double_up(agent, incentive):
    return (
        Sale.objects.approved().filter(agent=agent, incentive=incentive)
        .annotate(day=TruncDate("sold_at"))
        .values("day")
        .annotate(n=Count("id"))
        .filter(n__gte=2)
        .exists()
    )


def _task_check_big_ticket(agent, incentive):
    return Sale.objects.approved().filter(agent=agent, incentive=incentive, quantity__gte=3).exists()


def _task_check_weekly_warrior(agent, incentive):
    today = timezone.localdate()
    cutoff = min(today, incentive.period_end)
    elapsed_weeks = ((cutoff - incentive.period_start).days // 7) + 1
    if elapsed_weeks < 2:
        return False  # too early in the period for this one to mean anything yet
    sale_weeks = {
        (sold_at.date() - incentive.period_start).days // 7
        for sold_at in Sale.objects.approved().filter(agent=agent, incentive=incentive).values_list("sold_at", flat=True)
    }
    return set(range(elapsed_weeks)).issubset(sale_weeks)


def _task_check_full_lineup(agent, incentive):
    goal_product_ids = set(
        IncentiveProductGoal.objects.filter(incentive=incentive).values_list("product_id", flat=True)
    )
    if not goal_product_ids:
        return False
    sold_product_ids = set(
        Sale.objects.approved().filter(agent=agent, incentive=incentive).values_list("product_id", flat=True)
    )
    return goal_product_ids.issubset(sold_product_ids)


BONUS_TASKS = [
    {
        "key": "quick_starter",
        "name": "Quick Starter",
        "emoji": "🏃",
        "description": "Log a sale within the first 3 days of this incentive.",
        "points": 15,
        "check": _task_check_quick_starter,
    },
    {
        "key": "category_explorer",
        "name": "Category Explorer",
        "emoji": "🧭",
        "description": "Sell products from 2 different categories this period.",
        "points": 15,
        "check": _task_check_category_explorer,
    },
    {
        "key": "double_up",
        "name": "Double Up",
        "emoji": "✌️",
        "description": "Log 2 sales on the same day this period.",
        "points": 10,
        "check": _task_check_double_up,
    },
    {
        "key": "big_ticket",
        "name": "Big Ticket",
        "emoji": "🎟️",
        "description": "Log a single sale of 3 or more units.",
        "points": 10,
        "check": _task_check_big_ticket,
    },
    {
        "key": "weekly_warrior",
        "name": "Weekly Warrior",
        "emoji": "🗓️",
        "description": "Log at least one sale in every week of this incentive so far.",
        "points": 20,
        "check": _task_check_weekly_warrior,
    },
    {
        "key": "full_lineup",
        "name": "Full Lineup",
        "emoji": "🎛️",
        "description": "Sell every featured product in this incentive at least once.",
        "points": 25,
        "check": _task_check_full_lineup,
    },
]


def sync_bonus_tasks(agent, incentive):
    """Persist any quests the agent newly qualifies for this incentive.
    Returns the catalog entries (dicts, minus `check`) completed *this call*."""
    if not incentive:
        return []
    already = set(
        AgentTaskCompletion.objects.filter(agent=agent, incentive=incentive).values_list("key", flat=True)
    )
    newly_completed = []
    for task in BONUS_TASKS:
        if task["key"] in already:
            continue
        if task["check"](agent, incentive):
            AgentTaskCompletion.objects.get_or_create(
                agent=agent, incentive=incentive, key=task["key"], defaults={"points_awarded": task["points"]}
            )
            newly_completed.append({k: v for k, v in task.items() if k != "check"})
    return newly_completed


def bonus_tasks_context(agent, incentive):
    """The full quest checklist — done and not-yet-done — for rendering."""
    if not incentive:
        return []
    completed = {
        row["key"]: row["completed_at"]
        for row in AgentTaskCompletion.objects.filter(agent=agent, incentive=incentive).values(
            "key", "completed_at"
        )
    }
    return [
        {
            "key": t["key"],
            "name": t["name"],
            "emoji": t["emoji"],
            "description": t["description"],
            "points": t["points"],
            "done": t["key"] in completed,
            "completed_at": completed.get(t["key"]),
        }
        for t in BONUS_TASKS
    ]


def bonus_points_current(agent, incentive):
    """Bonus points banked from quests in the current incentive period."""
    if not incentive:
        return 0
    return (
        AgentTaskCompletion.objects.filter(agent=agent, incentive=incentive).aggregate(t=Sum("points_awarded"))["t"]
        or 0
    )


# ---------------------------------------------------------------------------
# Reward catalog — surfaces Tier.perk_description (already stored on every
# Tier, but never rendered anywhere until now) as a real "here's what you get"
# page, marked against the agent's progress in the current incentive.
# ---------------------------------------------------------------------------


def reward_catalog(agent, incentive):
    progress = tier_progress(agent, incentive) if incentive else None
    current_order = progress["current_tier"].order if progress and progress["current_tier"] else 0
    next_order = progress["next_tier"].order if progress and progress["next_tier"] else None
    return [
        {
            "tier": tier,
            "unlocked": tier.order <= current_order,
            "is_next": tier.order == next_order,
        }
        for tier in Tier.objects.all().order_by("order")
    ]


# ---------------------------------------------------------------------------
# Mystery box — a surprise bonus the moment a product goal is completed for
# the first time in an incentive period. Not a fixed-catalog concept like
# achievements/quests (there's no "check" to browse ahead of time) — it's
# reactive: for every goal currently complete, make sure a bonus has been
# awarded for it. AgentGoalBonus makes sure it only ever fires once per
# (agent, incentive, product), same get-or-create pattern as achievements.
#
# Sales now start "pending" and only affect goal completion once approved
# (see Sale.status), so a goal can flip to complete *between visits* — after
# an admin approves a backlog of sales, say — not only in the instant after
# a log-sale click. sync_goal_bonuses() is written to be called any time the
# dashboard loads, not just right after a sale, so that catch-up case still
# gets its celebratory moment the next time the agent opens the app.
# ---------------------------------------------------------------------------

MYSTERY_BOX_POINT_CHOICES = [10, 15, 20, 25]


def sync_goal_bonuses(agent, incentive):
    """Awards a bonus for every currently-complete goal that doesn't have one
    yet. Returns the boxes newly earned *this call* (usually empty)."""
    if not incentive:
        return []

    awarded = []
    for g in product_goal_progress(agent, incentive):
        if not g["complete"]:
            continue
        box, created = AgentGoalBonus.objects.get_or_create(
            agent=agent,
            incentive=incentive,
            product=g["product"],
            defaults={"points_awarded": random.choice(MYSTERY_BOX_POINT_CHOICES)},
        )
        if created:
            awarded.append({"product": g["product"].name, "points": box.points_awarded})
    return awarded


def public_teaser():
    """Aggregate, anonymous-safe stats shown on the (pre-login) login page —
    meant to hype up the current incentive before someone's even signed in."""
    incentive = get_active_incentive()
    if not incentive:
        return None

    week_ago = timezone.now() - timedelta(days=7)
    sales_this_week = (
        Sale.objects.approved().filter(incentive=incentive, sold_at__gte=week_ago).aggregate(q=Sum("quantity"))["q"] or 0
    )

    first_tier_rule = IncentiveTierRule.objects.filter(incentive=incentive).order_by("tier__order").first()
    leveled_up_count = 0
    if first_tier_rule:
        leveled_up_count = (
            Sale.objects.approved().filter(incentive=incentive)
            .values("agent")
            .annotate(total=Sum("points_earned"))
            .filter(total__gte=first_tier_rule.points_required)
            .count()
        )

    hot = (
        Sale.objects.approved().filter(incentive=incentive)
        .values("product__name")
        .annotate(units=Sum("quantity"))
        .order_by("-units")
        .first()
    )

    return {
        "incentive_name": incentive.name,
        "sales_this_week": sales_this_week,
        "leveled_up_count": leveled_up_count,
        "hot_product": hot["product__name"] if hot else None,
    }


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------


def leaderboard_rows(viewer, incentive, scope="region"):
    """Ranked standings for the current incentive. scope='region' limits to the
    viewer's own region; scope='company' is everyone. Agents with zero sales
    still appear (ranked last) — seeing you're not even on the board yet is
    itself a nudge to go log a sale."""
    if not incentive:
        return []

    agents_qs = AgentProfile.objects.select_related("user", "region")
    if scope == "region" and viewer.region_id:
        agents_qs = agents_qs.filter(region_id=viewer.region_id)
    agents = list(agents_qs)

    points_map = dict(
        Sale.objects.approved().filter(incentive=incentive, agent__in=agents)
        .values("agent")
        .annotate(total=Sum("points_earned"))
        .values_list("agent", "total")
    )

    tier_rules = list(
        IncentiveTierRule.objects.filter(incentive=incentive).select_related("tier").order_by("-tier__order")
    )

    def tier_for(points):
        for rule in tier_rules:
            if points >= rule.points_required:
                return rule.tier
        return None

    rows = []
    for a in agents:
        points = points_map.get(a.id, 0)
        tier = tier_for(points)
        rows.append(
            {
                "agent_id": a.id,
                "name": a.display_name,
                "avatar": a.avatar_emoji,
                "region": a.region.name if a.region else "—",
                "points": points,
                "tier": tier,
                "is_me": a.id == viewer.id,
            }
        )

    rows.sort(key=lambda r: -r["points"])
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows


def pace_comparison(agent):
    """'You're ahead' banner data: how this agent's points-so-far in the
    current incentive compare to where they were at the same number of days
    into the *previous* incentive. Returns None when there's no previous
    incentive to compare against (e.g. this is the very first one)."""
    current = get_active_incentive()
    if not current:
        return None

    previous = (
        Incentive.objects.filter(period_start__lt=current.period_start).order_by("-period_start").first()
    )
    if not previous:
        return None

    today = timezone.localdate()
    days_elapsed = max(0, (today - current.period_start).days)

    current_points = agent_points(agent, current)

    previous_cutoff = min(previous.period_start + timedelta(days=days_elapsed), previous.period_end)
    previous_points_to_date = (
        Sale.objects.approved().filter(agent=agent, incentive=previous, sold_at__date__lte=previous_cutoff).aggregate(
            total=Sum("points_earned")
        )["total"]
        or 0
    )

    if previous_points_to_date == 0:
        pct = None
    else:
        pct = round(((current_points - previous_points_to_date) / previous_points_to_date) * 100)

    return {
        "current_points": current_points,
        "previous_points_to_date": previous_points_to_date,
        "previous_name": previous.name,
        "pct": pct,
        "ahead": current_points >= previous_points_to_date,
    }


# ---------------------------------------------------------------------------
# Analyst / Director portals
#
# Phase 1 only ever built the Agent experience out in full. These two are
# deliberately minimal — a handful of real, live-queried numbers rather than
# a mockup — enough to prove the role-based login actually routes to a real,
# working page with real data, without pretending phase 2's incentive
# builder or approval-queue UI already exists.
# ---------------------------------------------------------------------------

def analyst_overview():
    """Read-only program-health snapshot for the Incentive Analyst portal."""
    incentive = get_active_incentive()
    agent_count = AgentProfile.objects.count()
    pending_count = Sale.objects.filter(status=Sale.STATUS_PENDING).count()

    overview = {
        "incentive": incentive,
        "agent_count": agent_count,
        "pending_count": pending_count,
        "total_points": 0,
        "total_units": 0,
        "region_rows": [],
        "top_product": None,
        "top_product_units": 0,
    }
    if not incentive:
        return overview

    approved = Sale.objects.approved().filter(incentive=incentive)
    overview["total_points"] = approved.aggregate(t=Sum("points_earned"))["t"] or 0
    overview["total_units"] = approved.aggregate(t=Sum("quantity"))["t"] or 0

    region_rows = (
        approved.values("agent__region__name").annotate(points=Sum("points_earned")).order_by("-points")
    )
    overview["region_rows"] = [
        {"name": r["agent__region__name"] or "Unassigned", "points": r["points"]} for r in region_rows
    ]

    top_product = approved.values("product__name").annotate(units=Sum("quantity")).order_by("-units").first()
    if top_product:
        overview["top_product"] = top_product["product__name"]
        overview["top_product_units"] = top_product["units"]

    return overview


def director_overview():
    """Snapshot for the Director portal. `pending_rows` is the actionable
    piece — each row carries its own `id`/`points` so the template can wire
    real Approve/Reject buttons straight to `views.api_review_sale`, no trip
    to the Django admin required (that's still available as a fallback for
    anything past the top 8 shown here)."""
    incentive = get_active_incentive()

    pending_qs = Sale.objects.filter(status=Sale.STATUS_PENDING).select_related("agent__user", "product")
    pending_count = pending_qs.count()
    pending_rows = [
        {
            "id": s.id,
            "agent": s.agent.display_name,
            "avatar": s.agent.avatar_emoji,
            "product": s.product.name,
            "quantity": s.quantity,
            "points": s.points_earned,
            "sold_at": s.sold_at,
        }
        for s in pending_qs.order_by("-sold_at")[:8]
    ]

    overview = {
        "incentive": incentive,
        "pending_rows": pending_rows,
        "pending_count": pending_count,
        "agent_count": AgentProfile.objects.count(),
        "total_points": 0,
        "top_agents": [],
    }
    if not incentive:
        return overview

    approved = Sale.objects.approved().filter(incentive=incentive)
    overview["total_points"] = approved.aggregate(t=Sum("points_earned"))["t"] or 0

    ranked = approved.values("agent").annotate(points=Sum("points_earned")).order_by("-points")[:5]
    agent_ids = [r["agent"] for r in ranked]
    agents_by_id = {a.id: a for a in AgentProfile.objects.select_related("user").filter(id__in=agent_ids)}
    overview["top_agents"] = [
        {
            "name": agents_by_id[r["agent"]].display_name,
            "avatar": agents_by_id[r["agent"]].avatar_emoji,
            "points": r["points"],
        }
        for r in ranked
        if r["agent"] in agents_by_id
    ]

    return overview

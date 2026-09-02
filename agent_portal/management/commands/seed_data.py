import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from agent_portal import insights
from agent_portal.models import (
    Region, Tier, Category, Product, Incentive,
    IncentiveTierRule, IncentiveProductGoal, AgentProfile, Sale, AgentAchievement, AgentTaskCompletion,
    AgentGoalBonus,
)
from agent_portal.roles import GROUP_ANALYST, GROUP_DIRECTOR

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds demo data: regions, tiers, products, an active monthly incentive, agents, and sales history."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete existing demo data first.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing existing agent_portal data...")
            AgentAchievement.objects.all().delete()
            AgentTaskCompletion.objects.all().delete()
            AgentGoalBonus.objects.all().delete()
            Sale.objects.all().delete()
            IncentiveProductGoal.objects.all().delete()
            IncentiveTierRule.objects.all().delete()
            Incentive.objects.all().delete()
            AgentProfile.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Tier.objects.all().delete()
            Region.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        regions = self._seed_regions()
        tiers = self._seed_tiers()
        categories, products = self._seed_products()
        incentives = self._seed_incentives(tiers, products)
        agents = self._seed_agents(regions)
        self._seed_sales(agents, products, incentives)
        self._seed_analyst_and_director()

        for agent in agents:
            insights.sync_achievements(agent)
            for incentive in incentives:
                insights.sync_bonus_tasks(agent, incentive)

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write("Agent logins: " + ", ".join(f"{a.user.username}/spectrum123" for a in agents))
        self.stdout.write("Incentive Analyst login: analyst1/spectrum123")
        self.stdout.write("Director login: director1/spectrum123")

    def _seed_regions(self):
        names = [("Northeast", "NE"), ("Southeast", "SE"), ("Midwest", "MW"), ("West", "WE")]
        regions = []
        for name, code in names:
            region, _ = Region.objects.get_or_create(name=name, defaults={"code": code})
            regions.append(region)
        return regions

    def _seed_tiers(self):
        specs = [
            ("Silver", 1, "🥈", "silver", "5% bonus commission"),
            ("Gold", 2, "🥇", "gold", "10% bonus commission + swag box"),
            ("Diamond", 3, "💎", "accent", "20% bonus commission + trip credit"),
        ]
        tiers = []
        for name, order, emoji, color, perk in specs:
            tier, _ = Tier.objects.get_or_create(
                name=name, defaults={"order": order, "emoji": emoji, "color": color, "perk_description": perk}
            )
            tiers.append(tier)
        return tiers

    def _seed_products(self):
        cat_specs = {
            "Internet": ["Fiber 500", "Fiber Gig", "Fiber Ultra 2-Gig"],
            "TV & Streaming": ["Core TV Bundle", "Sports Add-On", "Premium Streaming Bundle"],
            "Mobile": ["Unlimited Mobile Line", "Family Mobile Plan"],
            "Security": ["Home Security Starter", "Smart Home Security Pro"],
        }
        categories = {}
        products = []
        for cat_name, product_names in cat_specs.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            categories[cat_name] = category
            for name in product_names:
                product, _ = Product.objects.get_or_create(
                    name=name, defaults={"category": category, "base_points": random.choice([10, 15, 20, 25])}
                )
                products.append(product)
        return categories, products

    @staticmethod
    def _month_bounds(first_of_month):
        if first_of_month.month == 12:
            next_month = first_of_month.replace(year=first_of_month.year + 1, month=1)
        else:
            next_month = first_of_month.replace(month=first_of_month.month + 1)
        return first_of_month, next_month - timedelta(days=1)

    def _seed_incentives(self, tiers, products):
        """Every month gets its own campaign name, tier thresholds and featured
        products — incentives are meant to vary month to month."""
        today = timezone.localdate()
        this_month_start = today.replace(day=1)

        month_starts = []
        cursor = this_month_start
        for _ in range(3):  # this month + 2 previous
            month_starts.append(cursor)
            prev_month = cursor.month - 1 or 12
            prev_year = cursor.year - 1 if cursor.month == 1 else cursor.year
            cursor = cursor.replace(year=prev_year, month=prev_month)
        month_starts.reverse()  # oldest -> newest

        campaign_names = ["Fresh Start Push", "Mid-Year Momentum", "Growth Sprint"]
        threshold_variants = [
            {tiers[0]: 120, tiers[1]: 300, tiers[2]: 500},
            {tiers[0]: 150, tiers[1]: 350, tiers[2]: 600},
            {tiers[0]: 150, tiers[1]: 350, tiers[2]: 600},
        ]

        incentives = []
        for i, start in enumerate(month_starts):
            end = self._month_bounds(start)[1]
            is_current = start == this_month_start
            incentive, _ = Incentive.objects.get_or_create(
                name=f"{start:%B} {campaign_names[i % len(campaign_names)]}",
                defaults={
                    "period_start": start,
                    "period_end": end,
                    "description": "Push fiber upgrades and smart security bundles this period."
                    if is_current
                    else "Archived incentive period.",
                    "is_active": True,
                },
            )
            for tier, points in threshold_variants[i % len(threshold_variants)].items():
                IncentiveTierRule.objects.get_or_create(
                    incentive=incentive, tier=tier, defaults={"points_required": points}
                )

            featured = random.sample(products, k=min(5, len(products)))
            for product in featured:
                IncentiveProductGoal.objects.get_or_create(
                    incentive=incentive, product=product, defaults={"target_quantity": random.choice([3, 4, 5, 6])}
                )
            incentives.append(incentive)

        return incentives

    def _seed_agents(self, regions):
        names = [
            ("agent1", "Jordan", "Ramirez"),
            ("agent2", "Alex", "Chen"),
            ("agent3", "Riley", "Thompson"),
            ("agent4", "Sam", "Patel"),
            ("agent5", "Casey", "Nguyen"),
            ("agent6", "Morgan", "Diaz"),
        ]
        emojis = ["🚀", "⚡", "🌟", "🔥", "🎯", "🧠"]
        today = timezone.localdate()

        # Seed a mix of login-streak states so the Achievements tab (and the
        # header streak chip) shows some variety out of the box. agent1 is
        # deliberately left "yesterday" so logging in today visibly bumps it —
        # a nice live moment for a demo.
        streak_specs = [
            {"current": 4, "longest": 6, "last": today - timedelta(days=1)},   # agent1
            {"current": 7, "longest": 7, "last": today},                        # agent2 — Streak Legend
            {"current": 2, "longest": 3, "last": today},                        # agent3 — Streak Starter
            {"current": 0, "longest": 1, "last": today - timedelta(days=5)},    # agent4
            {"current": 1, "longest": 2, "last": today},                        # agent5
            {"current": 3, "longest": 4, "last": today},                        # agent6 — Streak Starter
        ]

        agents = []
        for i, (username, first, last) in enumerate(names):
            user, created = User.objects.get_or_create(
                username=username, defaults={"first_name": first, "last_name": last}
            )
            if created:
                user.set_password("spectrum123")
                user.save()
            streak = streak_specs[i % len(streak_specs)]
            profile, _ = AgentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "region": regions[i % len(regions)],
                    "avatar_emoji": emojis[i % len(emojis)],
                    "employee_code": f"SC-{1000 + i}",
                    "current_login_streak": streak["current"],
                    "longest_login_streak": streak["longest"],
                    "last_login_date": streak["last"],
                },
            )
            agents.append(profile)
        return agents

    def _seed_analyst_and_director(self):
        """One demo login for each of the other two portals — see
        agent_portal/roles.py for how a plain Django Group is enough to mark
        an account as one of these, since neither has per-user data (yet)
        the way AgentProfile does."""
        analyst_group, _ = Group.objects.get_or_create(name=GROUP_ANALYST)
        director_group, _ = Group.objects.get_or_create(name=GROUP_DIRECTOR)

        analyst, created = User.objects.get_or_create(
            username="analyst1", defaults={"first_name": "Avery", "last_name": "Kim"}
        )
        if created:
            analyst.set_password("spectrum123")
            analyst.save()
        analyst.groups.add(analyst_group)

        director, created = User.objects.get_or_create(
            username="director1", defaults={"first_name": "Devon", "last_name": "Brooks"}
        )
        if created:
            director.set_password("spectrum123")
            director.save()
        director.groups.add(director_group)

    def _seed_sales(self, agents, products, incentives):
        now = timezone.now()
        today = timezone.localdate()

        for incentive in incentives:
            goal_products = list(
                Product.objects.filter(incentiveproductgoal__incentive=incentive).distinct()
            ) or products

            is_current = incentive.period_start <= today <= incentive.period_end
            span_days = (incentive.period_end - incentive.period_start).days
            # for the current, still-open month only sell up through today
            usable_days = (today - incentive.period_start).days if is_current else span_days

            for agent in agents:
                num_sales = random.randint(4, 14)
                for _ in range(num_sales):
                    product = random.choice(goal_products)
                    quantity = random.choice([1, 1, 1, 2])
                    offset_days = random.randint(0, max(0, usable_days))
                    sold_at = timezone.make_aware(
                        timezone.datetime.combine(
                            incentive.period_start + timedelta(days=offset_days),
                            timezone.datetime.min.time(),
                        )
                    ) + timedelta(hours=random.randint(7, 20))
                    if sold_at > now:
                        sold_at = now
                    sale = Sale(
                        agent=agent,
                        product=product,
                        incentive=incentive,
                        quantity=quantity,
                        points_earned=0,
                        status=Sale.STATUS_APPROVED,
                        sold_at=sold_at,
                    )
                    sale.save()

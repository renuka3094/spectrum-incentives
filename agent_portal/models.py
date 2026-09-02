from django.conf import settings
from django.db import models
from django.utils import timezone


class Region(models.Model):
    """A geographic sales territory. Used to power the 'nearby agents' AI insights."""

    name = models.CharField(max_length=80, unique=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tier(models.Model):
    """A reward level (Silver / Gold / Diamond) an agent climbs within one incentive period."""

    name = models.CharField(max_length=40, unique=True)
    order = models.PositiveSmallIntegerField(help_text="1 = first tier, 2 = next, etc.")
    emoji = models.CharField(max_length=8, default="⭐")
    color = models.CharField(
        max_length=20,
        default="accent",
        help_text="CSS token used to color this tier's badge (see style.css).",
    )
    perk_description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """A sellable product or service (internet plan, mobile line, security bundle, etc.)."""

    name = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    base_points = models.PositiveIntegerField(
        default=10, help_text="Points earned per unit sold, unless overridden per incentive."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]

    def __str__(self):
        return self.name


class Incentive(models.Model):
    """A monthly incentive campaign. Targets and tier thresholds can change every month."""

    name = models.CharField(max_length=150)
    period_start = models.DateField()
    period_end = models.DateField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(Product, through="IncentiveProductGoal")
    tiers = models.ManyToManyField(Tier, through="IncentiveTierRule")

    class Meta:
        ordering = ["-period_start"]

    def __str__(self):
        return f"{self.name} ({self.period_start:%b %Y})"

    @property
    def is_current(self):
        today = timezone.localdate()
        return self.period_start <= today <= self.period_end


class IncentiveTierRule(models.Model):
    """How many points an agent needs to reach a given tier, for a specific incentive."""

    incentive = models.ForeignKey(Incentive, on_delete=models.CASCADE, related_name="tier_rules")
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    points_required = models.PositiveIntegerField()

    class Meta:
        unique_together = ("incentive", "tier")
        ordering = ["tier__order"]

    def __str__(self):
        return f"{self.incentive} → {self.tier}: {self.points_required} pts"


class IncentiveProductGoal(models.Model):
    """The recommended sell-through target for a product within one incentive period."""

    incentive = models.ForeignKey(Incentive, on_delete=models.CASCADE, related_name="product_goals")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    target_quantity = models.PositiveIntegerField(
        help_text="Suggested units to sell during this incentive period."
    )
    points_override = models.PositiveIntegerField(
        null=True, blank=True, help_text="Overrides the product's base points for this incentive only."
    )

    class Meta:
        unique_together = ("incentive", "product")

    def __str__(self):
        return f"{self.incentive} – {self.product} x{self.target_quantity}"

    @property
    def points_per_unit(self):
        return self.points_override or self.product.base_points


class AgentProfile(models.Model):
    """Extra, field-agent-specific data hung off the built-in Django User."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_profile")
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, related_name="agents")
    avatar_emoji = models.CharField(max_length=8, default="🚀")
    employee_code = models.CharField(max_length=20, unique=True)
    joined_on = models.DateField(default=timezone.localdate)

    # Daily login streak — separate from sales activity, rewards just showing up.
    current_login_streak = models.PositiveIntegerField(default=0)
    longest_login_streak = models.PositiveIntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username


class SaleQuerySet(models.QuerySet):
    def approved(self):
        """Everywhere a sale needs to actually *count* — points, tiers,
        goals, achievements, quests, the leaderboard, the activity ticker —
        should query through here, not the bare manager. A self-logged sale
        starts life as 'pending' (see Sale.STATUS_PENDING) and must not move
        any of those numbers until an admin approves it."""
        return self.filter(status=Sale.STATUS_APPROVED)


class Sale(models.Model):
    """A single logged sale, counted against whichever incentive is active at sold_at."""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="sales")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sales")
    incentive = models.ForeignKey(Incentive, on_delete=models.CASCADE, related_name="sales")
    quantity = models.PositiveIntegerField(default=1)
    points_earned = models.PositiveIntegerField()
    sold_at = models.DateTimeField(default=timezone.now)
    # Self-logged sales start "pending" and don't count toward anything until
    # an admin (standing in for the not-yet-built Director approval queue)
    # approves them — see SaleQuerySet.approved(). Seeded/admin-created sales
    # default to "approved" since they're already-trusted historical data.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_APPROVED)

    objects = SaleQuerySet.as_manager()

    class Meta:
        ordering = ["-sold_at"]

    def __str__(self):
        return f"{self.agent} sold {self.quantity}x {self.product} ({self.points_earned} pts, {self.status})"

    def save(self, *args, **kwargs):
        if not self.points_earned:
            goal = IncentiveProductGoal.objects.filter(incentive=self.incentive, product=self.product).first()
            per_unit = goal.points_per_unit if goal else self.product.base_points
            self.points_earned = per_unit * self.quantity
        super().save(*args, **kwargs)


class AgentAchievement(models.Model):
    """
    Records that an agent has permanently unlocked a badge.

    The catalog of badges (name, emoji, description, and the rule that unlocks
    it) lives in code as plain Python (see agent_portal/insights.py — ACHIEVEMENTS),
    not as a database table: badges are a fixed product concept, not something an
    analyst edits, so there's no admin-managed model for them. This table only
    stores the fact that a given agent earned a given badge `key`, and when.
    """

    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="achievements")
    key = models.CharField(max_length=50)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("agent", "key")
        ordering = ["-earned_at"]

    def __str__(self):
        return f"{self.agent} earned {self.key}"


class AgentTaskCompletion(models.Model):
    """
    Records that an agent completed a bite-sized bonus quest during a specific
    incentive period. The quest catalog (name, description, bonus points, and
    the rule that completes it) lives in code as plain Python — see
    agent_portal/insights.py — BONUS_TASKS, the same pattern as ACHIEVEMENTS.

    Unlike achievements (permanent, once-ever), quests reset every incentive
    period — "log a sale within 3 days" means 3 days into *this* incentive —
    so completion is keyed on (agent, incentive, key) rather than just
    (agent, key).
    """

    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="task_completions")
    incentive = models.ForeignKey(Incentive, on_delete=models.CASCADE, related_name="task_completions")
    key = models.CharField(max_length=50)
    points_awarded = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("agent", "incentive", "key")
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.agent} completed {self.key} ({self.incentive})"


class AgentGoalBonus(models.Model):
    """
    Records a one-time "mystery box" bonus awarded the instant an agent first
    completes a product goal within a given incentive. It's a celebratory
    surprise layered on top of the points already earned from the sale itself
    — the amount is picked at random from a small fixed range in
    insights.award_goal_mystery_boxes(), then persisted here so a goal that's
    already complete never re-awards on a later sale of the same product.
    """

    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="goal_bonuses")
    incentive = models.ForeignKey(Incentive, on_delete=models.CASCADE, related_name="goal_bonuses")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    points_awarded = models.PositiveIntegerField()
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("agent", "incentive", "product")
        ordering = ["-awarded_at"]

    def __str__(self):
        return f"{self.agent} mystery box for {self.product} ({self.points_awarded} pts)"

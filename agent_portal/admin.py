from django.contrib import admin
from django.utils import timezone

from . import models


@admin.register(models.Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "code")


@admin.register(models.Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "emoji", "color")


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "base_points", "is_active")
    list_filter = ("category", "is_active")


class IncentiveTierRuleInline(admin.TabularInline):
    model = models.IncentiveTierRule
    extra = 1


class IncentiveProductGoalInline(admin.TabularInline):
    model = models.IncentiveProductGoal
    extra = 1


@admin.register(models.Incentive)
class IncentiveAdmin(admin.ModelAdmin):
    list_display = ("name", "period_start", "period_end", "is_active", "is_current")
    inlines = [IncentiveTierRuleInline, IncentiveProductGoalInline]


@admin.register(models.AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "display_name", "region", "employee_code", "joined_on",
        "current_login_streak", "longest_login_streak",
    )
    list_filter = ("region",)


@admin.register(models.AgentAchievement)
class AgentAchievementAdmin(admin.ModelAdmin):
    list_display = ("agent", "key", "earned_at")
    list_filter = ("key",)


@admin.register(models.AgentTaskCompletion)
class AgentTaskCompletionAdmin(admin.ModelAdmin):
    list_display = ("agent", "key", "incentive", "points_awarded", "completed_at")
    list_filter = ("key", "incentive")


@admin.register(models.AgentGoalBonus)
class AgentGoalBonusAdmin(admin.ModelAdmin):
    list_display = ("agent", "product", "incentive", "points_awarded", "awarded_at")
    list_filter = ("incentive", "product")


@admin.register(models.AgentCleanStreakAward)
class AgentCleanStreakAwardAdmin(admin.ModelAdmin):
    list_display = ("agent", "streak_length", "points_awarded", "awarded_at")
    list_filter = ("streak_length",)


@admin.register(models.Sale)
class SaleAdmin(admin.ModelAdmin):
    """This is where self-logged sales actually get verified — a sale an
    agent submits through the app starts 'Pending review' and doesn't count
    toward anything (points, tiers, goals, badges, quests) until it's
    approved here. Select rows and use the actions below; this stands in
    for the Director approval queue that's planned for a later phase."""

    list_display = ("agent", "product", "incentive", "quantity", "points_earned", "status", "sold_at")
    list_filter = ("status", "incentive", "product__category")
    date_hierarchy = "sold_at"
    actions = ["approve_sales", "reject_sales"]

    @admin.action(description="Approve selected sales (counts them toward points/tiers/goals)")
    def approve_sales(self, request, queryset):
        updated = queryset.update(status=models.Sale.STATUS_APPROVED, reviewed_at=timezone.now())
        self.message_user(request, f"Approved {updated} sale(s).")

    @admin.action(description="Reject selected sales (they'll never count)")
    def reject_sales(self, request, queryset):
        updated = queryset.update(status=models.Sale.STATUS_REJECTED, reviewed_at=timezone.now())
        self.message_user(request, f"Rejected {updated} sale(s).")

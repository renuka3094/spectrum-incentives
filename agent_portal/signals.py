from datetime import timedelta

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone

from .models import AgentLoginDay

# Cap on stockpiled streak freezes. Without a cap, a long unbroken streak
# would earn one every 7 days forever and eventually make a missed day
# consequence-free for months — this keeps "don't break the chain" still
# meaningful while forgiving the occasional missed day.
MAX_STREAK_FREEZES = 3

# Award one streak freeze every this-many-days of an unbroken streak.
STREAK_FREEZE_MILESTONE = 7


@receiver(user_logged_in)
def update_login_streak(sender, user, request, **kwargs):
    """
    Every time someone actually logs in, bump (or reset) their daily streak.
    This is deliberately separate from the sales streak — it rewards just
    showing up and checking in, which is the whole point of the 'encourage
    them to log in' ask.

    Game Center additions on top of the original streak counters:
    - Every login day is also recorded as its own AgentLoginDay row, which is
      what draws the streak calendar heatmap (the counters alone can't
      reconstruct *which* days were active).
    - A single missed day no longer resets the streak to 1 if the agent has
      a streak freeze banked (see MAX_STREAK_FREEZES) — the freeze is spent
      automatically and the missed day is backfilled as a freeze-covered
      AgentLoginDay, so the calendar shows why the streak survived.
    - A freeze is earned automatically every STREAK_FREEZE_MILESTONE days of
      unbroken streak, up to the cap.
    """
    profile = getattr(user, "agent_profile", None)
    if profile is None:
        return

    today = timezone.localdate()

    if profile.last_login_date == today:
        return  # already counted today (e.g. a page refresh re-triggered login)

    yesterday = today - timedelta(days=1)
    # If last_login_date is two days back, exactly one day (yesterday) was
    # missed — that's the single day a freeze can cover.
    last_login_two_days_back = today - timedelta(days=2)

    if profile.last_login_date == yesterday:
        profile.current_login_streak += 1
    elif profile.last_login_date == last_login_two_days_back and profile.streak_freezes > 0:
        # Exactly one day was missed and a freeze is banked — spend it rather
        # than resetting. Backfill the skipped day (yesterday) so the
        # calendar shows it was freeze-covered, not actually logged in.
        profile.streak_freezes -= 1
        profile.current_login_streak += 1
        AgentLoginDay.objects.get_or_create(
            agent=profile, date=yesterday, defaults={"used_streak_freeze": True}
        )
    else:
        profile.current_login_streak = 1

    if profile.current_login_streak % STREAK_FREEZE_MILESTONE == 0:
        profile.streak_freezes = min(profile.streak_freezes + 1, MAX_STREAK_FREEZES)

    profile.longest_login_streak = max(profile.longest_login_streak, profile.current_login_streak)
    profile.last_login_date = today
    profile.save(
        update_fields=[
            "current_login_streak",
            "longest_login_streak",
            "last_login_date",
            "streak_freezes",
        ]
    )
    AgentLoginDay.objects.get_or_create(agent=profile, date=today)

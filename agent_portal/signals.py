from datetime import timedelta

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def update_login_streak(sender, user, request, **kwargs):
    """
    Every time someone actually logs in, bump (or reset) their daily streak.
    This is deliberately separate from the sales streak — it rewards just
    showing up and checking in, which is the whole point of the 'encourage
    them to log in' ask.
    """
    profile = getattr(user, "agent_profile", None)
    if profile is None:
        return

    today = timezone.localdate()

    if profile.last_login_date == today:
        return  # already counted today (e.g. a page refresh re-triggered login)
    elif profile.last_login_date == today - timedelta(days=1):
        profile.current_login_streak += 1
    else:
        profile.current_login_streak = 1

    profile.longest_login_streak = max(profile.longest_login_streak, profile.current_login_streak)
    profile.last_login_date = today
    profile.save(update_fields=["current_login_streak", "longest_login_streak", "last_login_date"])

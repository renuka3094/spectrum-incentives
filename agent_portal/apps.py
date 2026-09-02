from django.apps import AppConfig


class AgentPortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agent_portal"

    def ready(self):
        from . import signals  # noqa: F401  (registers the login-streak signal handler)

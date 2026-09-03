from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("analyst/", views.analyst_dashboard, name="analyst_dashboard"),
    path("director/", views.director_dashboard, name="director_dashboard"),
    path("no-role/", views.no_role, name="no_role"),
    path("api/log-sale/", views.api_log_sale, name="api_log_sale"),
    path("api/cancel-sale/<int:sale_id>/", views.api_cancel_sale, name="api_cancel_sale"),
    path("api/review-sale/<int:sale_id>/", views.api_review_sale, name="api_review_sale"),
    path("api/insights/", views.api_insights, name="api_insights"),
    path("api/activity/", views.api_activity, name="api_activity"),
    path("api/set-avatar/", views.api_set_avatar, name="api_set_avatar"),
]

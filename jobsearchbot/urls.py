from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from bot.views import telegram_webhook, health_check, status_page, robots_txt

urlpatterns = [
    path("", status_page, name="home"),
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("api/", include("bot.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("webhook/", telegram_webhook, name="telegram_webhook"),
    path("robots.txt", robots_txt, name="robots_txt"),
]

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from bot.views import telegram_webhook, paystack_callback
from bot.sitemaps import StaticViewSitemap
from bot.views import robots_txt  # 👈 Create this view as shown below

sitemaps_dict = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', telegram_webhook, name='telegram_webhook'),
    path('callback/', paystack_callback, name='paystack_callback'),

    # ✅ Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps_dict}, name='sitemap'),

    # ✅ Robots.txt
    path('robots.txt', robots_txt, name='robots_txt'),

    # ✅ Home page
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]
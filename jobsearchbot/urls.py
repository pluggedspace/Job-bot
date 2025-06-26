from django.contrib import admin
from django.urls import path, include
from bot.views import telegram_webhook, paystack_callback
from django.conf import settings

from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', telegram_webhook, name='telegram_webhook'),  # ✅ With trailing slash
    path('callback/', paystack_callback, name='paystack_callback'),
    
    # Serve index.html at root
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

]

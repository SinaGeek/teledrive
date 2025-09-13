# /home/Sina94/Teledrive/bot/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('policy', views.policy, name='policy'),
    path('terms', views.terms, name='terms'),
    path('login', views.login, name='login'),
    path('oauth/callback', views.oauth_callback, name='oauth_callback'),
    path('telegram/webhook', views.telegram_webhook, name='telegram_webhook'),
]
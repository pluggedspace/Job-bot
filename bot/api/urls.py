"""
URL Configuration for Job Bot API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bot.api.views import (
    UserProfileView,
    LinkAccountView,
    LinkedAccountsView,
    UnlinkAccountView,
    JobSearchView,
    SavedJobsView,
    AlertViewSet,
)
from bot.api.career_views import CareerPathView, UpskillPlanView
from bot.api.interview_views import InterviewPracticeView, InterviewSessionView
from bot.api.cv_views import CVReviewView, CoverLetterView
from bot.api.subscription_views import CreateSubscriptionView, VerifyPaymentView, QuotaView
from bot.api.whatsapp_webhook import WhatsAppWebhookView


# Router for viewsets
router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')

urlpatterns = [
    # User profile
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Account linking
    path('account/link/', LinkAccountView.as_view(), name='link-account'),
    path('account/linked/', LinkedAccountsView.as_view(), name='linked-accounts'),
    path('account/unlink/', UnlinkAccountView.as_view(), name='unlink-account'),
    
    # Jobs
    path('jobs/search/', JobSearchView.as_view(), name='job-search'),
    path('jobs/saved/', SavedJobsView.as_view(), name='saved-jobs'),
    
    # Career growth
    path('career/path/', CareerPathView.as_view(), name='career-path'),
    path('career/upskill/', UpskillPlanView.as_view(), name='upskill-plan'),
    
    # Interview practice
    path('interview/practice/', InterviewPracticeView.as_view(), name='interview-practice'),
    path('interview/session/', InterviewSessionView.as_view(), name='interview-session'),
    
    # CV enhancements
    path('cv/review/', CVReviewView.as_view(), name='cv-review'),
    path('cv/coverletter/', CoverLetterView.as_view(), name='cover-letter'),
    
    # Subscription and payment
    path('subscription/create/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('subscription/verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('subscription/quota/', QuotaView.as_view(), name='quota'),
    
    # WhatsApp webhook
    path('whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
    
    # Include router URLs (alerts)
    path('', include(router.urls)),
]

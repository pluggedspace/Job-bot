"""
URL Configuration for Job Bot API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bot.api.views import UserProfileView, JobSearchView, SavedJobsView, AlertViewSet
from bot.api.career_views import CareerPathView, UpskillPlanView
from bot.api.interview_views import InterviewPracticeView, InterviewSessionView
from bot.api.cv_views import CVReviewView, CoverLetterView
from bot.api.subscription_views import CreateSubscriptionView, VerifyPaymentView, QuotaView
from bot.api.whatsapp_webhook import WhatsAppWebhookView

router = DefaultRouter()
router.register(r"alerts", AlertViewSet, basename="alert")

urlpatterns = [
    path("user/profile/", UserProfileView.as_view(), name="user-profile"),
    path("jobs/search/", JobSearchView.as_view(), name="job-search"),
    path("jobs/saved/", SavedJobsView.as_view(), name="saved-jobs"),
    path("career/path/", CareerPathView.as_view(), name="career-path"),
    path("career/upskill/", UpskillPlanView.as_view(), name="upskill-plan"),
    path("interview/practice/", InterviewPracticeView.as_view(), name="interview-practice"),
    path("interview/session/", InterviewSessionView.as_view(), name="interview-session"),
    path("cv/review/", CVReviewView.as_view(), name="cv-review"),
    path("cv/coverletter/", CoverLetterView.as_view(), name="cover-letter"),
    path("subscription/create/", CreateSubscriptionView.as_view(), name="create-subscription"),
    path("subscription/verify/", VerifyPaymentView.as_view(), name="verify-payment"),
    path("subscription/quota/", QuotaView.as_view(), name="quota"),
    path("whatsapp/webhook/", WhatsAppWebhookView.as_view(), name="whatsapp-webhook"),
    path("", include(router.urls)),
]

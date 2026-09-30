from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from .models import (
    AIConversation, ActivityLog, AnalyticsEvent, Appointment, Certificate,
    ContactMessage, Education, Experience, Integration, LegalPage, MediaAsset,
    NewsletterSubscriber, Page, Post, Profile, Project, Section, Service,
    SiteSettings, Skill, SocialLink, Testimonial, AutomationRule,
    WebhookEndpoint,
)


class CommandCenterSite(AdminSite):
    site_header = "SEID DIGITAL · COMMAND CENTER"
    site_title = "Seid Digital Control Center"
    index_title = "Platform Overview"
    site_url = "/"
    enable_nav_sidebar = True

    def index(self, request, extra_context=None):
        now = timezone.now()
        stats = {
            "projects": Project.objects.count(),
            "services": Service.objects.count(),
            "posts": Post.objects.count(),
            "messages": ContactMessage.objects.count(),
            "appointments": Appointment.objects.count(),
            "certificates": Certificate.objects.count(),
            "subscribers": NewsletterSubscriber.objects.filter(active=True).count(),
            "ai_questions": AIConversation.objects.count(),
            "pageviews": AnalyticsEvent.objects.filter(event_type="pageview").count(),
            "scheduled": Post.objects.filter(status="scheduled").count(),
        }
        recent_messages = ContactMessage.objects.order_by("-created_at")[:6]
        recent_activity = ActivityLog.objects.select_related("user").order_by("-created_at")[:8]
        upcoming = Appointment.objects.filter(date__gte=now).order_by("date")[:5]
        context = {
            "dashboard_stats": stats,
            "recent_messages": recent_messages,
            "recent_activity": recent_activity,
            "upcoming_appointments": upcoming,
        }
        if extra_context:
            context.update(extra_context)
        return super().index(request, extra_context=context)


command_center = CommandCenterSite(name="admin")

# Keep account management inside the same premium control center.
from django.contrib.auth.admin import UserAdmin, GroupAdmin  # noqa: E402

command_center.register(get_user_model(), UserAdmin)
command_center.register(Group, GroupAdmin)

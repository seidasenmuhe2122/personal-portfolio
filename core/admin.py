from django.contrib import admin
from django.utils.html import format_html

from .admin_site import command_center
from .forms import PageAdminForm, PostAdminForm, LegalPageAdminForm, SectionAdminForm
from .models import *


def thumb(obj, field="image"):
    value = getattr(obj, field, None)
    if not value:
        return "—"
    try:
        return format_html('<img src="{}" style="width:52px;height:38px;object-fit:cover;border-radius:8px;border:1px solid #26334d">', value.url)
    except Exception:
        return "—"


class BaseAdmin(admin.ModelAdmin):
    list_per_page = 25
    save_on_top = True
    empty_value_display = "—"


@admin.register(SiteSettings, site=command_center)
class SiteSettingsAdmin(BaseAdmin):
    list_display = ("site_name", "ai_enabled", "blog_enabled", "analytics_enabled", "appointments_enabled", "updated_at")
    fieldsets = (
        ("Brand & Identity", {"fields": ("site_name", "tagline", "logo", "favicon", "contact_orbit_mark", "contact_orbit_image", "primary_color", "accent_color", "dark_mode_default")} ),
        ("Feature Switchboard", {"fields": ("ai_enabled", "blog_enabled", "comments_enabled", "registration_enabled", "maintenance_mode", "telegram_enabled", "github_enabled", "analytics_enabled", "appointments_enabled", "newsletter_enabled")} ),
        ("SEO & Social Preview", {"fields": ("meta_title", "meta_description", "meta_keywords", "og_image")} ),
        ("Contact & Social", {"fields": ("email", "phone", "location", "github_url", "linkedin_url", "telegram_url", "facebook_url", "instagram_url", "youtube_url")} ),
        ("Footer & Maintenance", {"fields": ("footer_text", "maintenance_message")} ),
    )


@admin.register(Profile, site=command_center)
class ProfileAdmin(BaseAdmin):
    list_display = ("name", "headline", "email", "location", "availability", "updated_at")
    search_fields = ("name", "headline", "bio", "email")
    readonly_fields = ("photo_preview",)
    fieldsets = (
        ("Portfolio profile", {"fields": ("name", "headline", "bio")} ),
        ("Portrait & CV", {
            "fields": ("photo_preview", "photo", "portrait_width", "portrait_height", "cv"),
            "description": "Upload or replace the homepage portrait. Set its desktop width and height in pixels; smaller screens scale it to fit. Use Clear to remove it.",
        }),
        ("Contact details", {"fields": ("email", "phone", "location", "availability")} ),
        ("Online profiles", {"fields": ("github", "linkedin", "telegram", "website")} ),
    )

    @admin.display(description="Current portrait")
    def photo_preview(self, obj):
        if not obj or not obj.photo:
            return "No portrait uploaded yet."
        try:
            return format_html(
                '<img src="{}" alt="Current profile portrait" style="width:160px;height:200px;object-fit:cover;border-radius:16px;border:2px solid #26334d">',
                obj.photo.url,
            )
        except Exception:
            return "The saved portrait could not be displayed."


@admin.register(Skill, site=command_center)
class SkillAdmin(BaseAdmin):
    list_display = ("name", "category", "level", "featured", "order")
    list_filter = ("featured", "category")
    search_fields = ("name", "category")
    list_editable = ("level", "featured", "order")
    ordering = ("order", "name")


@admin.register(Service, site=command_center)
class ServiceAdmin(BaseAdmin):
    list_display = ("title", "featured", "published", "order", "updated_at")
    list_filter = ("published", "featured")
    search_fields = ("title", "summary", "description")
    list_editable = ("featured", "published", "order")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Project, site=command_center)
class ProjectAdmin(BaseAdmin):
    list_display = ("preview", "title", "featured", "published", "order", "updated_at")
    list_filter = ("published", "featured")
    search_fields = ("title", "summary", "description", "technologies", "github_repo")
    list_editable = ("featured", "published", "order")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ()
    preview = lambda self, obj: thumb(obj)
    preview.short_description = "Preview"


@admin.register(Certificate, site=command_center)
class CertificateAdmin(BaseAdmin):
    list_display = ("title", "issuer", "issue_date", "featured", "order")
    list_filter = ("featured", "issuer")
    search_fields = ("title", "issuer", "credential_id")
    list_editable = ("featured", "order")


@admin.register(Experience, site=command_center)
class ExperienceAdmin(BaseAdmin):
    list_display = ("role", "organization", "start_date", "end_date", "current", "location")
    list_filter = ("current", "organization")
    search_fields = ("role", "organization", "description")


@admin.register(Education, site=command_center)
class EducationAdmin(BaseAdmin):
    list_display = ("degree", "institution", "field", "start_date", "end_date", "current")
    list_filter = ("current", "institution")
    search_fields = ("degree", "institution", "field")


@admin.register(Testimonial, site=command_center)
class TestimonialAdmin(BaseAdmin):
    list_display = ("name", "role", "company", "published", "order")
    list_filter = ("published",)
    search_fields = ("name", "role", "company", "quote")
    list_editable = ("published", "order")


@admin.register(Page, site=command_center)
class PageAdmin(BaseAdmin):
    form = PageAdminForm
    list_display = ("title", "slug", "published", "menu", "order", "updated_at")
    list_filter = ("published", "menu")
    search_fields = ("title", "content", "seo_title", "seo_description")
    list_editable = ("published", "menu", "order")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Section, site=command_center)
class SectionAdmin(BaseAdmin):
    form = SectionAdminForm
    list_display = ("name", "section_type", "enabled", "order", "updated_at")
    list_filter = ("enabled", "section_type")
    search_fields = ("name", "title", "subtitle", "content")
    list_editable = ("enabled", "order")
    ordering = ("order", "id")


@admin.register(Post, site=command_center)
class PostAdmin(BaseAdmin):
    form = PostAdminForm
    list_display = ("title", "post_type", "status", "publish_at", "author", "updated_at")
    list_filter = ("status", "post_type", "author")
    search_fields = ("title", "body", "tags", "seo_title", "seo_description")
    list_editable = ("status", "publish_at")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    autocomplete_fields = ("author",)


@admin.register(LegalPage, site=command_center)
class LegalPageAdmin(BaseAdmin):
    form = LegalPageAdminForm
    list_display = ("title", "slug", "published", "updated_at")
    list_filter = ("published",)
    search_fields = ("title", "content")
    list_editable = ("published",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ContactMessage, site=command_center)
class ContactMessageAdmin(BaseAdmin):
    list_display = ("name", "email", "subject", "read", "replied", "created_at")
    list_filter = ("read", "replied", "created_at")
    search_fields = ("name", "email", "subject", "message")
    list_editable = ("read", "replied")
    readonly_fields = ("ip_address", "created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(Appointment, site=command_center)
class AppointmentAdmin(BaseAdmin):
    list_display = ("name", "email", "topic", "date", "status", "created_at")
    list_filter = ("status", "date")
    search_fields = ("name", "email", "topic", "notes")
    list_editable = ("status",)
    date_hierarchy = "date"


@admin.register(NewsletterSubscriber, site=command_center)
class NewsletterSubscriberAdmin(BaseAdmin):
    list_display = ("email", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("email",)
    list_editable = ("active",)


@admin.register(MediaAsset, site=command_center)
class MediaAssetAdmin(BaseAdmin):
    list_display = ("title", "folder", "uploaded_by", "created_at")
    list_filter = ("folder",)
    search_fields = ("title", "alt_text", "caption", "folder")
    autocomplete_fields = ("uploaded_by",)


@admin.register(SocialLink, site=command_center)
class SocialLinkAdmin(BaseAdmin):
    list_display = ("name", "icon", "enabled", "order")
    list_filter = ("enabled",)
    search_fields = ("name", "url", "icon")
    list_editable = ("icon", "enabled", "order")
    ordering = ("order", "id")


@admin.register(AutomationRule, site=command_center)
class AutomationRuleAdmin(BaseAdmin):
    list_display = ("name", "event", "action", "enabled", "last_run")
    list_filter = ("enabled", "event", "action")
    search_fields = ("name", "event", "action", "last_error")
    list_editable = ("enabled",)


@admin.register(Integration, site=command_center)
class IntegrationAdmin(BaseAdmin):
    list_display = ("provider", "enabled", "public_identifier", "last_sync")
    list_filter = ("enabled", "provider")
    search_fields = ("provider", "public_identifier", "last_error")
    list_editable = ("enabled",)


@admin.register(AnalyticsEvent, site=command_center)
class AnalyticsEventAdmin(BaseAdmin):
    list_display = ("event_type", "path", "session_key", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("path", "referrer", "session_key")
    readonly_fields = ("created_at", "updated_at", "ip_hash")
    date_hierarchy = "created_at"


@admin.register(AIConversation, site=command_center)
class AIConversationAdmin(BaseAdmin):
    list_display = ("question_short", "provider", "success", "created_at")
    list_filter = ("provider", "success")
    search_fields = ("question", "answer")
    readonly_fields = ("session_key", "question", "answer", "provider", "success", "created_at", "updated_at")

    def question_short(self, obj):
        return obj.question[:80]
    question_short.short_description = "Question"


@admin.register(ActivityLog, site=command_center)
class ActivityLogAdmin(BaseAdmin):
    list_display = ("user", "action", "path", "ip_address", "created_at")
    list_filter = ("created_at",)
    search_fields = ("action", "path", "ip_address", "user__username")
    readonly_fields = tuple(f.name for f in ActivityLog._meta.fields)
    date_hierarchy = "created_at"


@admin.register(WebhookEndpoint, site=command_center)
class WebhookEndpointAdmin(BaseAdmin):
    list_display = ("name", "url", "enabled", "last_sent", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("name", "url", "events", "last_error")
    list_editable = ("enabled",)

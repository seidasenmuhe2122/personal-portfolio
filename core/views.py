import hashlib
import json
import logging
import os
from pathlib import Path
from .automation import run_automation

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .forms import AppointmentForm, ContactForm, NewsletterForm
from .models import *
from .sanitizers import sanitize_plain_text
from .services.ai_service import AIService

logger = logging.getLogger(__name__)

GEMINI_FALLBACK_MESSAGE = "AI assistant is temporarily unavailable. Please try again."

def _portfolio_ai_system_prompt(profile, site):
    owner_name = profile.name if profile else "not listed"
    site_name = site.site_name if site else "Seid Digital Platform"
    details = [
        f"Owner: {owner_name}",
        f"Headline: {profile.headline if profile else ''}",
        f"Biography: {profile.bio[:1800] if profile else ''}",
    ]
    skills = list(Skill.objects.order_by("order", "name").values_list("name", flat=True)[:20])
    details.append("Skills: " + (", ".join(skills) if skills else "not listed"))

    projects = Project.objects.filter(published=True).order_by("-featured", "order", "title")[:8]
    details.append("Projects: " + ("; ".join(f"{item.title}: {item.summary} ({item.technologies})" for item in projects) or "not listed"))

    services = Service.objects.filter(published=True).order_by("-featured", "order", "title")[:8]
    details.append("Services: " + ("; ".join(f"{item.title}: {item.summary}" for item in services) or "not listed"))

    experience = Experience.objects.order_by("-start_date", "organization")[:8]
    details.append("Experience: " + ("; ".join(f"{item.role} at {item.organization}: {item.description[:240]}" for item in experience) or "not listed"))

    education = Education.objects.order_by("-start_date", "institution")[:8]
    details.append("Education: " + ("; ".join(f"{item.degree} in {item.field} at {item.institution}" for item in education) or "not listed"))

    certificates = Certificate.objects.order_by("-issue_date", "order", "title")[:12]
    details.append("Certificates: " + ("; ".join(f"{item.title} from {item.issuer}" for item in certificates) or "not listed"))

    contact_email = (site.email if site else "") or (profile.email if profile else "")
    contact_phone = (site.phone if site else "") or (profile.phone if profile else "")
    details.append("Public contact: " + ", ".join(value for value in (contact_email, contact_phone) if value) or "use the contact page")

    return (
        f"You are the website assistant for {site_name}. Answer clearly and professionally. "
        "Use only the portfolio facts below. Do not invent projects, credentials, contact details, or personal history. "
        "When requested information is absent, say it is unavailable and direct the visitor to the contact page. "
        "Portfolio facts:\n" + "\n".join(details)
    )[:8000]


def live_posts(location=None, limit=None):
    qs = Post.objects.filter(status="published").order_by("-created_at")
    if location:
        posts = []
        for post in qs:
            locations = post.locations if isinstance(post.locations, list) else []
            if location in locations:
                posts.append(post)
                if limit and len(posts) >= limit:
                    break
        return posts
    return qs[:limit] if limit else qs


def home(request):
    profile = Profile.objects.first()
    site = SiteSettings.objects.first()
    return render(request, "core/home.html", {
        "profile": profile,
        "projects": Project.objects.filter(published=True).order_by("-featured", "order", "-created_at")[:6],
        "skills": Skill.objects.filter(featured=True).order_by("order", "name"),
        "services": Service.objects.filter(published=True).order_by("-featured", "order")[:6],
        "experience": Experience.objects.all().order_by("-start_date")[:5],
        "education": Education.objects.all().order_by("-start_date")[:4],
        "certificates": Certificate.objects.all().order_by("-issue_date", "order")[:8],
        "testimonials": Testimonial.objects.filter(published=True).order_by("order")[:6],
        "posts": live_posts(limit=3),
        "sections": list(Section.objects.filter(enabled=True)),
        "stats": {
            "projects": Project.objects.filter(published=True).count(),
            "skills": Skill.objects.count(),
            "certificates": Certificate.objects.count(),
            "services": Service.objects.filter(published=True).count(),
        },
        "site_ready": bool(site),
    })


def about(request):
    return render(request, "core/about.html", {
        "profile": Profile.objects.first(),
        "skills": Skill.objects.all(),
        "experience": Experience.objects.all().order_by("-start_date"),
        "education": Education.objects.all().order_by("-start_date"),
        "certificates": Certificate.objects.all().order_by("-issue_date"),
        "testimonials": Testimonial.objects.filter(published=True),
    })


def projects(request):
    return render(request, "core/projects.html", {"projects": Project.objects.filter(published=True).order_by("-featured", "order", "-created_at")})


def project_detail(request, slug):
    return render(request, "core/project_detail.html", {"project": get_object_or_404(Project, slug=slug, published=True)})


def services(request):
    return render(request, "core/services.html", {"services": Service.objects.filter(published=True).order_by("-featured", "order")})


def blog(request):
    return render(request, "core/blog.html", {"posts": live_posts()})


def post_detail(request, slug):
    return render(request, "core/post_detail.html", {"post": get_object_or_404(Post, slug=slug, status="published")})


def page(request, slug):
    return render(request, "core/page.html", {"page": get_object_or_404(Page, slug=slug, published=True)})


def legal(request, slug):
    return render(request, "core/legal.html", {"page": get_object_or_404(LegalPage, slug=slug, published=True)})


def contact(request):
    form = ContactForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        msg = form.save(commit=False)
        msg.ip_address = request.META.get("REMOTE_ADDR")
        msg.save()

        run_automation(
            "contact_created",
            {
                "recipient": getattr(
                    settings,
                    "ADMIN_NOTIFICATION_EMAIL",
                    "",
                ),
                "subject": f"New Contact Message: {msg.subject}",
                "message": (
                    f"Name: {msg.name}\n"
                    f"Email: {msg.email}\n"
                    f"Subject: {msg.subject}\n\n"
                    f"Message:\n{msg.message}"
                ),
            },
        )

        AnalyticsEvent.objects.create(
            event_type="contact",
            path=request.path,
            session_key=request.session.session_key or "",
        )

        try:
            recipient = getattr(
                settings,
                "ADMIN_NOTIFICATION_EMAIL",
                "",
            )

            if recipient:
                send_mail(
                    f"New Contact Message: {msg.subject}",
                    (
                        f"Name: {msg.name}\n"
                        f"Email: {msg.email}\n"
                        f"Subject: {msg.subject}\n\n"
                        f"Message:\n{msg.message}"
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient],
                    fail_silently=False,
                    headers={
                        "Reply-To": msg.email,
                    },
                )
        except Exception:
            logger.exception(
                "Failed to send contact notification email."
            )

        messages.success(
            request,
            "Your message has been received. Thank you.",
        )
        return redirect("contact")

    return render(
        request,
        "core/contact.html",
        {
            "form": form,
            "profile": Profile.objects.first(),
        },
    )
def appointment(request):
    form = AppointmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        appointment_obj = form.save()
        AnalyticsEvent.objects.create(event_type="contact", path=request.path, session_key=request.session.session_key or "", metadata={"type": "appointment", "id": appointment_obj.pk})
        messages.success(request, "Your appointment request has been received. I will confirm the time with you.")
        return redirect("appointment")
    return render(request, "core/appointment.html", {"form": form})


@csrf_protect
@require_POST
def newsletter(request):
    form = NewsletterForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "message": "Please enter a valid email address."}, status=400)
    form.save()
    return JsonResponse({"ok": True, "message": "You're subscribed. Thank you!"})


@require_GET
def download_cv(request):
    profile = Profile.objects.first()
    if not profile or not profile.cv:
        raise Http404("CV is not available yet.")
    AnalyticsEvent.objects.create(event_type="download", path=request.path, session_key=request.session.session_key or "", metadata={"file": "cv"})
    return FileResponse(profile.cv.open("rb"), as_attachment=True, filename=Path(profile.cv.name).name)


@require_GET
def track(request):
    path = (request.GET.get("path") or request.POST.get("path") or "")[:500]
    raw = request.META.get("REMOTE_ADDR", "") + "|" + os.getenv("ANALYTICS_SALT", "local")
    AnalyticsEvent.objects.create(
        event_type="pageview",
        path=path,
        referrer=request.META.get("HTTP_REFERER", "")[:500],
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
        session_key=request.session.session_key or "",
        ip_hash=hashlib.sha256(raw.encode()).hexdigest(),
    )
    return JsonResponse({"ok": True})


@csrf_protect
@require_POST
def ai_chat(request):
    payload = {}
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid JSON request."}, status=400)
    elif request.POST:
        payload = request.POST

    q = sanitize_plain_text(payload.get("message") if isinstance(payload, dict) else request.POST.get("message", ""))
    if not q:
        return JsonResponse({"error": "Message required."}, status=400)
    if len(q) > 1200:
        return JsonResponse({"error": "Please keep your question under 1200 characters."}, status=400)

    identity = request.session.session_key or request.META.get("REMOTE_ADDR", "anonymous")
    key = f"ai-rate:{hashlib.sha256(identity.encode()).hexdigest()}"
    count = cache.get(key, 0)
    if count >= 12:
        return JsonResponse({"error": "Please wait a little before sending more questions."}, status=429)
    cache.set(key, count + 1, 300)

    profile = Profile.objects.first()
    site = SiteSettings.objects.first()
    system_prompt = _portfolio_ai_system_prompt(profile, site)
    messages = [{"role": "user", "content": q}]
    try:
        result = AIService(fallback_message=GEMINI_FALLBACK_MESSAGE).generate_response(messages, system_prompt)
    except Exception as exc:
        logger.warning("AI service failed: exception=%s", exc.__class__.__name__)
        result = {
            "success": False,
            "provider": "fallback",
            "text": GEMINI_FALLBACK_MESSAGE,
            "attempts": [{"provider": "service", "exception": exc.__class__.__name__, "error": "Unexpected AI service failure."}],
        }

    answer = sanitize_plain_text(result.get("text") or GEMINI_FALLBACK_MESSAGE)
    provider = result.get("provider") or "fallback"
    success = bool(result.get("success")) and provider != "fallback"

    AIConversation.objects.create(
        session_key=request.session.session_key or "",
        question=q,
        answer=sanitize_plain_text(answer),
        provider=provider,
        success=success,
    )
    AnalyticsEvent.objects.create(event_type="ai", path=request.path, session_key=request.session.session_key or "", metadata={"provider": provider})

    response_data = {
        "success": success,
        "reply": answer,
        "answer": answer,
        "provider": provider,
    }
    debug_requested = request.GET.get("debug") == "1" or request.headers.get("X-AI-Debug") == "1"
    if settings.DEBUG and debug_requested and not success:
        response_data["debug"] = {"attempts": result.get("attempts", [])}
    return JsonResponse(response_data)

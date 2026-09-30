from .models import Page, Post, SiteSettings, SocialLink


def _posts_at_location(location, limit=5):
    posts = Post.objects.filter(status="published").order_by("-created_at")
    matched = []
    for post in posts:
        locations = post.locations if isinstance(post.locations, list) else []
        if location in locations:
            matched.append(post)
            if len(matched) >= limit:
                break
    return matched


def site_settings(request):
    site = SiteSettings.objects.first() or SiteSettings()
    return {
        "site": site,
        "social_links": SocialLink.objects.filter(enabled=True).order_by("order", "id"),
        "menu_pages": Page.objects.filter(published=True, menu=True).order_by("order", "title"),
        "sidebar_posts": _posts_at_location("sidebar"),
    }

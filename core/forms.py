from django import forms
from django.utils import timezone
from .models import ContactMessage, Appointment, NewsletterSubscriber, Page, Post, LegalPage, Section
from .sanitizers import sanitize_plain_text, sanitize_rich_text


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "subject": forms.TextInput(attrs={"placeholder": "What would you like to discuss?"}),
            "message": forms.Textarea(attrs={"placeholder": "Tell me about your idea, project or question…", "rows": 8}),
        }

    def clean_message(self):
        value = sanitize_plain_text(self.cleaned_data["message"])
        if len(value) < 10:
            raise forms.ValidationError("Please add a little more detail so I can understand your request.")
        return value

    def clean_name(self):
        return sanitize_plain_text(self.cleaned_data["name"])

    def clean_subject(self):
        return sanitize_plain_text(self.cleaned_data["subject"])


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ("name", "email", "phone", "date", "topic", "notes")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "Phone (optional)", "autocomplete": "tel"}),
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "topic": forms.TextInput(attrs={"placeholder": "What should we discuss?"}),
            "notes": forms.Textarea(attrs={"placeholder": "Context, goals or questions…", "rows": 6}),
        }

    def clean_date(self):
        value = self.cleaned_data["date"]
        if value <= timezone.now():
            raise forms.ValidationError("Please choose a future date and time.")
        return value

    def clean_name(self):
        return sanitize_plain_text(self.cleaned_data["name"])

    def clean_phone(self):
        return sanitize_plain_text(self.cleaned_data["phone"])

    def clean_topic(self):
        return sanitize_plain_text(self.cleaned_data["topic"])

    def clean_notes(self):
        return sanitize_plain_text(self.cleaned_data["notes"])


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ("email",)
        widgets = {"email": forms.EmailInput(attrs={"placeholder": "Your email address", "autocomplete": "email"})}


class SanitizedRichTextAdminForm(forms.ModelForm):
    rich_text_fields = ()

    def clean(self):
        cleaned_data = super().clean()
        for field_name in self.rich_text_fields:
            if field_name in cleaned_data:
                cleaned_data[field_name] = sanitize_rich_text(cleaned_data[field_name])
        return cleaned_data


class PageAdminForm(SanitizedRichTextAdminForm):
    rich_text_fields = ("content",)

    class Meta:
        model = Page
        fields = "__all__"


class PostAdminForm(SanitizedRichTextAdminForm):
    rich_text_fields = ("body",)

    class Meta:
        model = Post
        fields = "__all__"


class LegalPageAdminForm(SanitizedRichTextAdminForm):
    rich_text_fields = ("content",)

    class Meta:
        model = LegalPage
        fields = "__all__"


class SectionAdminForm(SanitizedRichTextAdminForm):
    rich_text_fields = ("content",)

    class Meta:
        model = Section
        fields = "__all__"

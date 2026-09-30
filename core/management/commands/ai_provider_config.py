from django.core.management.base import BaseCommand

from core.services.ai_service import get_ai_configuration


class Command(BaseCommand):
    help = "Show AI provider configuration without displaying credentials."

    def handle(self, *args, **options):
        config = get_ai_configuration()
        self.stdout.write(f"Gemini configured: {config['gemini_configured']}")
        self.stdout.write(f"Groq configured: {config['groq_configured']}")
        self.stdout.write(f"OpenRouter configured: {config['openrouter_configured']}")
        self.stdout.write(f"Gemini model: {config['gemini_model']}")
        self.stdout.write(f"Groq model: {config['groq_model']}")
        self.stdout.write(f"OpenRouter model: {config['openrouter_model']}")
        self.stdout.write(f"Provider order: {','.join(config['provider_order'])}")
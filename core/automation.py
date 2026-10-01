import logging
from django.conf import settings
from django.utils import timezone
from .models import AutomationRule

logger = logging.getLogger(__name__)


def run_automation(event, data=None):
    data = data or {}

    rules = AutomationRule.objects.filter(
        enabled=True,
        event=event,
    )

    for rule in rules:
        try:
            if rule.action == "send_email":
                logger.info(
                    "Email automation skipped to prevent SMTP blocking: %s",
                    data,
                )

            elif rule.action == "log":
                logger.info(
                    "Automation '%s' executed for event '%s': %s",
                    rule.name,
                    event,
                    data,
                )

            else:
                raise ValueError(
                    f"Unsupported automation action: {rule.action}"
                )

            rule.last_run = timezone.now()
            rule.last_error = ""
            rule.save(update_fields=["last_run", "last_error"])

        except Exception as exc:
            rule.last_error = str(exc)
            rule.save(update_fields=["last_error"])
            logger.exception(
                "Automation rule '%s' failed.",
                rule.name,
            )
            continue

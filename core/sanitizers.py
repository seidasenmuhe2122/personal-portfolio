import html

import bleach


RICH_TEXT_TAGS = {
    "a", "blockquote", "br", "code", "em", "h2", "h3", "h4", "h5",
    "hr", "li", "ol", "p", "pre", "strong", "ul",
}
RICH_TEXT_ATTRIBUTES = {"a": ["href", "title"]}
RICH_TEXT_PROTOCOLS = {"http", "https", "mailto"}


def sanitize_rich_text(value):
    return bleach.clean(
        value or "",
        tags=RICH_TEXT_TAGS,
        attributes=RICH_TEXT_ATTRIBUTES,
        protocols=RICH_TEXT_PROTOCOLS,
        strip=True,
    )


def sanitize_plain_text(value):
    cleaned = bleach.clean(value or "", tags=set(), attributes={}, strip=True)
    return html.unescape(cleaned).strip()
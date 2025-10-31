"""
Custom template tags for rendering markdown in templates.

Usage in templates:
    {% load markdown_extras %}
    {{ comment.text|markdown }}
"""

from django import template
from django.utils.safestring import mark_safe
import markdown as md

register = template.Library()


@register.filter(name='markdown')
def markdown_format(text):
    """
    Convert markdown text to HTML.

    Uses the markdown library with safe extensions:
    - fenced_code: GitHub-style code blocks with ```
    - tables: Support for markdown tables
    - nl2br: Convert newlines to <br> tags
    - codehilite: Syntax highlighting for code blocks

    Args:
        text: Markdown-formatted text

    Returns:
        Safe HTML string
    """
    if not text:
        return ""

    # Configure markdown with useful extensions
    html = md.markdown(
        text,
        extensions=[
            'fenced_code',      # GitHub-style code blocks with ```
            'tables',           # Support for tables
            'nl2br',            # Convert newlines to <br>
            'codehilite',       # Syntax highlighting
            'sane_lists',       # Better list handling
        ],
        output_format='html5'
    )

    return mark_safe(html)

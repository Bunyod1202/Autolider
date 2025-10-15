from django import template
import re

register = template.Library()


@register.filter
def strip_num_prefix(value: str):
    """Remove leading underscore+digits+underscore like _2_, _10_."""
    try:
        return re.sub(r'^_*\d+_*\s*', '', str(value))
    except Exception:
        return value


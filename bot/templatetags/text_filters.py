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


@register.filter
def percent_in_parens(value: str):
    """Extract percentage number from strings like '14/40 ... (35.0%)'.
    Returns a string without the percent sign, rounded to .0 if needed.
    """
    try:
        m = re.search(r"\(([-+]?[0-9]+(?:[\.,][0-9]+)?)\s*%?\)", str(value))
        if not m:
            return ''
        num = m.group(1).replace(',', '.')
        v = float(num)
        if abs(v - round(v)) < 1e-6:
            return str(int(round(v)))
        return f"{v:.1f}"
    except Exception:
        return ''

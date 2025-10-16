from django import template
import re

register = template.Library()


@register.filter
def strip_num_prefix(value):
    """Remove leading underscore+digits+underscore like _2_, _10_."""
    if not value:
        return ''
    try:
        return re.sub(r'^_*\d+_*\s*', '', str(value))
    except Exception:
        return str(value)


@register.filter
def percent_in_parens(value):
    """Extract percentage number from strings like '14/40 ... (35.0%)'."""
    try:
        m = re.search(r"\(([-+]?[0-9]+(?:[\.,][0-9]+)?)\s*%?\)", str(value))
        if not m:
            return ''
        v = float(m.group(1).replace(',', '.'))
        return str(int(round(v))) if abs(v - round(v)) < 1e-6 else f"{v:.1f}".rstrip('0').rstrip('.')
    except Exception:
        return ''


@register.filter
def correct_count(value):
    """Return the first integer before a slash."""
    try:
        s = str(value)
        m = re.match(r"\s*(\d+)\s*/", s)
        if m:
            return m.group(1)
        m2 = re.search(r"\d+", s)
        return m2.group(0) if m2 else ''
    except Exception:
        return ''


@register.filter
def complement_100(value):
    try:
        v = float(str(value).replace(',', '.'))
        res = 100 - v
        return str(int(round(res))) if abs(res - round(res)) < 1e-6 else f"{res:.1f}".rstrip('0').rstrip('.')
    except Exception:
        return '100'


@register.filter
def total_count(value):
    """Return denominator after slash, or second number found."""
    try:
        s = str(value)
        m = re.search(r'\d+\s*/\s*(\d+)', s)
        if m:
            return m.group(1)
        nums = re.findall(r'\d+', s)
        return nums[1] if len(nums) > 1 else (nums[0] if nums else '')
    except Exception:
        return ''

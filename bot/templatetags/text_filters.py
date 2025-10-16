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


@register.filter
def correct_count(value: str):
    """Extract the first integer (numerator) before a slash from strings like
    '14/40 savoldan (35.0%)' and return it as a string. Falls back to the
    first integer found if no slash is present.
    """
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
        if abs(res - round(res)) < 1e-6:
            return int(round(res))
        return f"{res:.1f}"
    except Exception:
        return 100


@register.filter
def total_count(value: str):
    try:
        s = str(value)
        m = re.search(r'\d+\s*/\s*(\d+)', s) # captures number after the slash
        if m:
            return m.group(1)
        # Fallback: second number in the string
        nums = re.findall(r'\d+', s)
        return nums[1] if len(nums) > 1 else (nums[0] if nums else '')
    except Exception:
        return ''

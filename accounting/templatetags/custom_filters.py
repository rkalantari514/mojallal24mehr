from django import template

register = template.Library()

@register.filter
def accounting_format(value):
    if value is None:
        return ""
    try:
        value = float(value)
        if value < 0:
            return f"({abs(value):,.2f})"  # نمایش اعداد منفی در پرانتز با ۲ رقم اعشار
        return f"{value:,.2f}"  # نمایش اعداد مثبت با ۲ رقم اعشار
    except (ValueError, TypeError):
        return value

# your_app/templatetags/custom_filters.py
# your_app/templatetags/custom_filters.py
from django import template
import locale

register = template.Library()

@register.filter
def intcomma_custom(value):
    locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    return locale.format_string("%d", value, grouping=True)



from django import template

register = template.Library()

@register.filter
def percentage(value):
    return "{:.0f}".format(value * 100)



from django import template
from django.utils import timezone
import math

register = template.Library()

@register.filter
def days_diff(value, arg=None):
    """
    Calculates the difference in days between two dates.
    If 'value' is a date and 'arg' is a date, returns (value - arg).days
    If 'arg' is None, returns (value - today).days
    """
    if not value:
        return None

    if arg is None:
        compare_date = timezone.now().date()
    else:
        compare_date = arg

    if isinstance(value, timezone.datetime):
        value_date = value.date()
    else:
        value_date = value # Assume it's already a date object

    if isinstance(compare_date, timezone.datetime):
        compare_date = compare_date.date()

    delta = value_date - compare_date
    return delta.days

@register.filter
def abs_days_diff(value, arg=None):
    """
    Calculates the absolute difference in days between two dates.
    If 'value' is a date and 'arg' is a date, returns abs((value - arg).days)
    If 'arg' is None, returns abs((value - today).days)
    """
    days = days_diff(value, arg)
    if days is not None:
        return abs(days)
    return None
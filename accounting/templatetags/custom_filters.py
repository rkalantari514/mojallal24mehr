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

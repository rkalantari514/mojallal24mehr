# your_app/templatetags/custom_filters.py

from django import template
from django.contrib import humanize
from django.utils import timezone
import locale


register = template.Library()

# فیلتر برای فرمت ارقام حسابداری
@register.filter
def accounting_format(value):
    if value is None:
        return ""
    try:
        value = float(value)
        if value < 0:
            return f"({abs(value):,.2f})"  # اعداد منفی در پرانتز و با ۲ رقم اعشار
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value

# فیلتر برای جدا کردن ارقام با کاما سازگار با Locale
@register.filter
def intcomma_custom(value):
    try:
        locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')
    except locale.Error:
        # در سیستم‌هایی که این locale نصب نیست، به حالت پیش‌فرض برمی‌گردد
        pass
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    return locale.format_string("%d", value, grouping=True)

# فیلتر برای درصد
@register.filter
def percentage(value):
    try:
        return "{:.0f}".format(value * 100)
    except (ValueError, TypeError):
        return value

# فیلتر برای تفاوت روزها بین دو تاریخ
@register.filter
def days_diff(value, arg=None):
    if not value:
        return None
    if arg is None:
        compare_date = timezone.now().date()
    else:
        compare_date = arg
    # اگر مقدار اولیه datetime باشد، به تاریخ تبدیل کن
    if hasattr(value, 'date'):
        value_date = value.date()
    else:
        value_date = value
    if hasattr(compare_date, 'date'):
        compare_date = compare_date.date()
    delta = value_date - compare_date
    return delta.days

# فیلتر برای تفاوت مطلق روزها
@register.filter
def abs_days_diff(value, arg=None):
    days = days_diff(value, arg)
    if days is not None:
        return abs(days)
    return None





@register.filter
def index(List, i):
    try:
        return List[i]
    except:
        return ''






from django import template
from django.template.defaultfilters import floatformat


@register.filter
def custom_intword(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value

    sign = '-' if value < 0 else '+'
    abs_value = abs(value)

    # اگر عدد کمتر از ۱ میلیون باشد، همان مقدار را برمی‌گردانیم
    if abs_value < 1_000_000:
        return str(value)

    units = [
        (10**9, 'میلیارد'),
        (10**6, 'میلیون'),
        (10**3, 'هزار'),
    ]

    def round_one_decimal(v):
        return round(v, 1)

    for multiplier, unit_name in units:
        if abs_value >= multiplier:
            number = abs_value / multiplier
            rounded_number = round_one_decimal(number)
            # ساختن رشته نهایی با علامت منفی در ابتدای عدد
            return f"{floatformat(rounded_number, 1)} {sign} {unit_name} تومان "

    # اگر هیچکدام از شرط‌ها برقرار نشد، عدد اولیه را برمی‌گردانیم
    return str(value)
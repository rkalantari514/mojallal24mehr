# your_app/templatetags/custom_filters.py

from django import template
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

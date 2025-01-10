from django import template

register = template.Library()

@register.filter
def accounting_format(value):
    if value is None:
        return ""
    try:
        value = float(value)
        if value < 0:
            return f"({abs(value):,.0f})"  # نمایش اعداد منفی در پرانتز
        return f"{value:,.0f}"  # نمایش اعداد مثبت به صورت معمولی
    except (ValueError, TypeError):
        return value
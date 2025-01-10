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
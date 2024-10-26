from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import FactorDetaile, Factor, Kala, Kardex  # اطمینان حاصل کنید که مدل‌ها را وارد کرده‌اید

# @receiver(pre_save, sender=FactorDetaile)
def set_factor_and_kala(sender, instance, **kwargs):
    print("Signal set_factor_and_kala triggered")  # برای دیباگینگ

    # پیدا کردن factor براساس code_factor
    if instance.code_factor:
        try:
            factor = Factor.objects.get(code=instance.code_factor)
        except Factor.DoesNotExist:
            factor = None
    else:
        factor = None

    # پیدا کردن kala براساس code_kala
    if instance.code_kala:
        try:
            kala = Kala.objects.get(code=instance.code_kala)
        except Kala.DoesNotExist:
            kala = None
    else:
        kala = None

    # بررسی تغییرات و تنظیم مقادیر جدید فقط در صورت تغییر
    if instance.factor != factor:
        instance.factor = factor
    if instance.kala != kala:
        instance.kala = kala


# @receiver(pre_save, sender=Kardex)
def update_kardex_codes(sender, instance, **kwargs):
    print("Signal update_kardex_codes triggered")  # برای دیباگینگ

    if not instance.pk:
        # رکورد جدید است، تنظیم اولیه
        try:
            instance.factor = Factor.objects.get(code=instance.code_factor)
        except Factor.DoesNotExist:
            instance.factor = None

        try:
            instance.kala = Kala.objects.get(code=instance.code_kala)
        except Kala.DoesNotExist:
            instance.kala = None

        if instance.kala:
            instance.code_kala = instance.kala.code
        if instance.factor:
            instance.code_factor = instance.factor.code
        return  # خروج از تابع برای رکوردهای جدید

    try:
        old_instance = Kardex.objects.get(pk=instance.pk)
    except Kardex.DoesNotExist:
        old_instance = None

    if old_instance and (old_instance.code_factor != instance.code_factor or old_instance.code_kala != instance.code_kala):
        try:
            factor = Factor.objects.get(code=instance.code_factor)
        except Factor.DoesNotExist:
            factor = None

        try:
            kala = Kala.objects.get(code=instance.code_kala)
        except Kala.DoesNotExist:
            kala = None

        # بررسی تغییرات و تنظیم مقادیر جدید فقط در صورت تغییر
        if instance.factor != factor:
            instance.factor = factor
        if instance.kala != kala:
            instance.kala = kala
        if instance.kala:
            instance.code_kala = instance.kala.code
        if instance.factor:
            instance.code_factor = instance.factor.code

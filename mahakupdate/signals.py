from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import FactorDetaile, Factor, Kala, Kardex  # اطمینان حاصل کنید که مدل‌ها را وارد کرده‌اید

# @receiver(pre_save, sender=FactorDetaile)
# def set_factor_and_kala(sender, instance, **kwargs):
#     # پیدا کردن factor براساس code_factor
#     try:
#         instance.factor = Factor.objects.get(code=instance.code_factor)
#     except Factor.DoesNotExist:
#         instance.factor = None  # اگر پیدا نشد None قرار بده
#
#     # پیدا کردن kala براساس code_kala
#     try:
#         instance.kala = Kala.objects.get(code=instance.code_kala)
#     except Kala.DoesNotExist:
#         instance.kala = None  # اگر پیدا نشد None قرار بده


# @receiver(pre_save, sender=Kardex)
# def update_kardex_codes(sender, instance, **kwargs):
#     # استفاده از یک کوئری واحد برای پیدا کردن عوامل و کالاها
#
#     if not instance.is_prioritized:
#         return  # از اینجا خارج می‌شود و دیگر کد اجرا نمی‌شود
#
#
#     if not hasattr(instance, '_fetched_related'):
#         instance._fetched_related = True
#         instance.factor = Factor.objects.filter(code=instance.code_factor).first()
#         instance.kala = Kala.objects.filter(code=instance.code_kala).first()
#
#









    # print(f'Updating Kardex codes for: {instance}')
    # if instance.kala:
    #     instance.code_kala = instance.kala.code
    #     print(f'Updated code_kala to: {instance.code_kala}')
    # else:
    #     print('Instance kala is None')
    #
    # if instance.factor:
    #     instance.code_factor = instance.factor.code
    #     print(f'Updated code_factor to: {instance.code_factor}')
    # else:
    #     print('Instance factor is None')
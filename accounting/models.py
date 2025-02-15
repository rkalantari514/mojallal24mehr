from django.db import models

from mahakupdate.models import Person, Loan


# Create your models here.


# class BedehiMoshtari(models.Model):
#     tafzili = models.IntegerField(blank=True, null=True, verbose_name='تفصیلی')
#     person=models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True)
#     total_mandeh = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مانده کل')
#     loans=models.ManyToManyField(Loan, blank=True)
#
#
#
#
#
#     sharh = models.CharField(max_length=255, null=True, verbose_name='شرح')
#     bed = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='بدهکار')
#     bes = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='بستانکار')
#     sanad_code = models.IntegerField(null=True, verbose_name='کد سند')
#     sanad_type = models.IntegerField(null=True, verbose_name='نوع سند')
#     meghdar = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مقدار')
#     syscomment = models.CharField(max_length=255, null=True, verbose_name='عنوان سند')
#     curramount = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مانده')
#     usercreated = models.CharField(max_length=255, null=True, verbose_name='ایجاد کننده')
#     is_analiz = models.BooleanField(default=False, verbose_name='آنالیز شده است')
#     cheque_id = models.CharField(blank=True, null=True, max_length=255,
#                                  verbose_name="شناسه چک")  # یا مقدار max_length مناسب
#     is_active = models.BooleanField(default=True, verbose_name='فعال است')
#
#     class Meta:
#         unique_together = (('code', 'radif'),)  # تعریف کلید یگانه
#         verbose_name = 'جزئیات سند'
#         verbose_name_plural = 'جزئیات اسناد'
#
#     def __str__(self):
#         return f"{self.code}-{self.radif}"

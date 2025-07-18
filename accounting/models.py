from django.db import models

from mahakupdate.models import Person, Loan


# Create your models here.


class BedehiMoshtari(models.Model):
    tafzili = models.IntegerField(blank=True, null=True, verbose_name='تفصیلی')
    moin = models.IntegerField(blank=True, null=True, verbose_name='معین')
    person=models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True)
    total_mandeh = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مانده کل')
    loans=models.ManyToManyField(Loan, blank=True)
    loans_total=models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مجموع  وام ها')
    total_with_loans=models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='برآیند بدهی با وام')
    from_last_daryaft=models.IntegerField(default=None,blank=True, null=True, verbose_name='از آخری دریافت')
    sleep_investment = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='خواب سرمایه')

    class Meta:
        verbose_name = 'بدهی مشتری'
        verbose_name_plural = 'بدهی مشتریان'

    def __str__(self):
        return f"{self.tafzili}-"
        # return f"{self.tafzili}-{self.person.lname}"

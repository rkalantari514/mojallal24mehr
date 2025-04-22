import os

from django.db import models

# Create your models here.

def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext

def upload_image_path(instance, filename):
    name, ext = get_filename_ext(filename)
    final_name = f"{instance.id}{ext}"
    return f"site/{final_name}"



from django.utils import timezone



class MasterInfo(models.Model):
    acc_year = models.IntegerField(blank=True, null=True,verbose_name='سال مالی')
    company_name= models.CharField(max_length=255, null=True,verbose_name='نام شرکت')
    company_logo1 = models.ImageField(upload_to=upload_image_path, null=True, blank=True, verbose_name='لوگوی اصلی')
    is_active = models.BooleanField(default=False, verbose_name='فعال است؟')
    last_report_time=models.DateTimeField(blank=True, null=True,verbose_name='زمان آخرین ارسال گزاش')
    last_update_time = models.DateTimeField(default=timezone.now, verbose_name='زمان آخرین آپدیت')

    active_day=models.IntegerField(default=0,blank=True, null=True,verbose_name='روز فعال')


    sayer_hazine_ave = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='متوسط سایر هزینه ها')
    sayer_daramad_ave = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='متوسط  سایر درآمد ها')

    sood_navizhe_min = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ناویژه کمترین')
    sood_navizhe_max = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ناویژه بیشترین')
    sood_navizhe_ave = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ناویژه میانگین')
    sood_navizhe_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ناویژه کل')

    sood_vizhe_min = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ویژه کمترین')
    sood_vizhe_max = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ویژه بیشترین')
    sood_vizhe_ave = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ویژه میانگین')
    sood_vizhe_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ویژه کل')



    asnad_daryaftani = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='اسناد دریافتنی')
    asnad_pardakhtani = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='اسناد پرداختنی')


    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'انواع تنظیمات'

    def __str__(self):
        return str(self.acc_year)




class MasterReport(models.Model):
    day = models.DateField(verbose_name='روز')
    total_mojodi = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='کل موجودی')
    value_of_purchased_goods = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='ارزش کالای خریداری شده')
    khales_forosh = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='خالص فروش')
    baha_tamam_forosh = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='بهای تمام شده کالای فروخته شده')
    sayer_hazine = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سایر هزینه ها')
    sayer_daramad = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سایر درآمد ها')
    sood_navizhe = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ناویژه')
    sood_vizhe = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ویژه')
    asnad_daryaftani = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='اسناد دریافتنی')
    asnad_pardakhtani = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='اسناد پرداختنی')
    # daramad_forosh = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='درآمد از فروش')


    total_delaycost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='کل اقساط معوق')
    total_mtday = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='خواب تعویق')




    class Meta:
        verbose_name = 'گزارش کلی'
        verbose_name_plural = 'گزارش‌های کلی'

    def __str__(self):
        return f"گزارش روز {self.day}"


class MonthlyReport(models.Model):
    #
    year=models.IntegerField(blank=True, null=True,verbose_name='سال')
    month=models.IntegerField(blank=True, null=True,verbose_name='شماره ماه')
    month_name=models.CharField(max_length=255, null=True,verbose_name='ماه')
    month_first_day=models.DateField(verbose_name='روز اول ماه')
    month_last_day=models.DateField(verbose_name='روز آخر ماه')


    # data
    total_mojodi = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='کل موجودی')
    value_of_purchased_goods = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='ارزش کالای خریداری شده')
    khales_forosh = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='خالص فروش')
    baha_tamam_forosh = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='بهای تمام شده کالای فروخته شده')
    sayer_hazine = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سایر هزینه ها')
    sayer_daramad = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سایر درآمد ها')
    sood_navizhe = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ناویژه')
    sood_vizhe = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='سود ویژه')
    asnad_daryaftani = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='اسناد دریافتنی')
    asnad_pardakhtani = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='اسناد پرداختنی')
    # daramad_forosh = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='درآمد از فروش')

    class Meta:
        verbose_name = 'گزارش ماهانه'
        verbose_name_plural = 'گزارش‌های ماهانه'

    def __str__(self):
        return f"گزارش ماه {self.month_name} سال {self.year}"




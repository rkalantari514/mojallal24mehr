from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
import jdatetime
from django.utils import timezone


# Create your models here.


class Mtables(models.Model):
    in_use = models.BooleanField(default=False, verbose_name='در حال استفاده است')
    none_use = models.BooleanField(default=False, verbose_name=' بدون استفاده')
    name = models.CharField(blank = True,null = True,max_length=150, verbose_name='نام جدول')
    description = models.CharField(blank = True,null = True,max_length=150, verbose_name='توضیح')
    row_count = models.IntegerField(blank = True,null = True,default=0, verbose_name='تعداد ردیف ها')
    cloumn_count = models.IntegerField(blank = True,null = True,default=0, verbose_name='تعداد ستون ها')
    last_update_time = models.DateTimeField(default=timezone.now, blank=True, null=True, verbose_name='آخرین آپدیت')
    update_period = models.IntegerField(default=60, blank=True, null=True, verbose_name='بازه به‌روزرسانی (دقیقه)')
    update_duration = models.FloatField(blank=True, null=True, verbose_name='مدت زمان به‌روزرسانی (ثانیه)')
    update_priority = models.IntegerField(default=0, blank=True, null=True, verbose_name='اولویت آپدیت')


    class Meta:
        verbose_name = 'جدول محک'
        verbose_name_plural = 'جداول محک'
        ordering = ['update_priority']
    def __str__(self):
        return self.name

class KalaGroupinfo(models.Model):
    code= models.IntegerField(default=0, verbose_name='کد اطلاعات گروه بندی')
    cat1=models.CharField(max_length=150,blank=True, null=True, default="", verbose_name='دسته بندی 1')
    cat2=models.CharField(max_length=150,blank=True, null=True, default="", verbose_name='دسته بندی 2')
    cat3=models.CharField(max_length=150,blank=True, null=True, default="", verbose_name='دسته بندی 3')
    contain=models.CharField(max_length=300,blank=True, verbose_name='شامل باشد')
    not_contain=models.CharField(max_length=300,blank=True,  verbose_name='شامل نباشد')

    class Meta:
        verbose_name = 'شرط گروه بندی کالا'
        verbose_name_plural = 'شروط گروه بندی کالا'

    def __str__(self):
        return self.contain


class Category(models.Model):
    LEVEL_CHOICES = (
        (1, 'سطح 1'),
        (2, 'سطح 2'),
        (3, 'سطح 3'),
    )
    name = models.CharField(max_length=150, verbose_name='نام دسته‌بندی')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='children', null=True, blank=True, verbose_name='دسته‌بندی والد')
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, verbose_name='سطح')

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name



class Kala(models.Model):
    code= models.IntegerField(default=0, verbose_name='کد کالا')
    name = models.CharField(max_length=150, verbose_name='نام کالا')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='kalas', verbose_name='دسته‌بندی',blank = True,null = True)


    class Meta:
        verbose_name = 'کالا'
        verbose_name_plural = 'کالاها'

    def __str__(self):
        return self.name


class Factor(models.Model):
    code= models.IntegerField(blank = True,null = True,default=0, verbose_name='شماره فاکتور')
    pdate = models.CharField(blank = True,null = True,max_length=150, verbose_name='تاریخ شمسی')
    mablagh_factor= models.FloatField(blank = True,null = True,default=0, verbose_name='مبلغ فاکتور')
    takhfif= models.FloatField(blank = True,null = True,default=0, verbose_name='تخفیف')
    create_time=models.CharField(blank = True,null = True,max_length=150,verbose_name='ساعت ایجاد')
    darsad_takhfif= models.FloatField(blank = True,null = True,default=0, verbose_name='درصد تخفیف')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ میلادی')

    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'

    def __str__(self):
        return self.pdate








class FactorDetaile(models.Model):
    code_factor = models.IntegerField(blank=True, null=True, default=0, verbose_name='شماره فاکتور')
    radif= models.IntegerField(blank = True,null = True,default=0, verbose_name='ردیف')
    factor = models.ForeignKey(Factor, on_delete=models.SET_NULL, related_name='details', null=True, blank = True)
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL, null=True)
    count = models.FloatField(blank=True, null=True, default=0, verbose_name='تعداد')
    mablagh_vahed = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ واحد')
    mablagh_nahaee = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ نهایی')

    class Meta:
        verbose_name = 'جزئیات فاکتور'
        verbose_name_plural = 'جزئیات فاکتور ها'

    def __str__(self):
        return str(self.code_factor)  # تصحیح به str

class Kardex(models.Model):
    pdate=models.CharField(blank = True,null = True,max_length=150, verbose_name='تاریخ شمسی')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ میلادی')
    percode=models.IntegerField(blank = True,null = True,default=0, verbose_name='کد شخص')
    warehousecode=models.IntegerField(blank = True,null = True,default=0, verbose_name='کد انبار')
    mablaghsanad=models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ سند')
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    radif = models.IntegerField(blank=True, null=True, default=0, verbose_name='ردیف در فاکتور')  #برای سورت کردن لازم است
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL,blank=True, null=True)
    code_factor=models.IntegerField(blank=True, null=True, default=0, verbose_name='کد فاکتور')
    factor = models.ForeignKey(Factor, on_delete=models.SET_NULL,blank=True, null=True)
    count=models.FloatField(blank=True, null=True, default=0, verbose_name='تعداد')
    averageprice=models.FloatField(blank=True, null=True, default=0, verbose_name='قیمت میانگین')
    stock=models.FloatField(blank=True, null=True, default=0, verbose_name='موجودی')
    is_prioritized = models.BooleanField(default=False)


    class Meta:
        verbose_name = 'کاردکس انبار'
        verbose_name_plural = 'کاردکس های انبار'
        ordering = ['-pdate', '-radif']

    def __str__(self):
        return str(self.pdate)  # تصحیح به str



# @receiver(pre_save, sender=Kardex)
@receiver(pre_save, sender=Factor)
def convert_pdate_to_date(sender, instance, **kwargs):
    print("Signal convert_pdate_to_date triggered")  # برای دیباگینگ

    if not instance.pk:
        # رکورد جدید است، تبدیل تاریخ
        if instance.pdate:
            jalali_date = jdatetime.date(*map(int, instance.pdate.split('/')))
            instance.date = jalali_date.togregorian()
    else:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            old_instance = None

        if old_instance and instance.pdate != old_instance.pdate:
            # تاریخ تغییر کرده، تبدیل تاریخ
            if instance.pdate:
                jalali_date = jdatetime.date(*map(int, instance.pdate.split('/')))
                instance.date = jalali_date.togregorian()


class PersonGroup(models.Model):
    code= models.IntegerField(default=0, verbose_name='کد گروه')
    name = models.CharField(max_length=150, verbose_name='نام گروه')

    class Meta:
        verbose_name = 'گروه'
        verbose_name_plural = 'گروه ها'
    def __str__(self):
        return self.name


class Person(models.Model):
    code= models.IntegerField(default=0, verbose_name='کد فرد')
    grpcode=models.IntegerField(default=0, verbose_name='کد گروه')
    group=models.ForeignKey(PersonGroup, on_delete=models.SET_NULL,blank=True, null=True)
    name = models.CharField(max_length=150, verbose_name='نام')
    lname = models.CharField(max_length=150, verbose_name='نام خانوادگی')
    tel1 = models.CharField(max_length=150, verbose_name='تلفن1')
    tel2 = models.CharField(max_length=150, verbose_name='تلفن2')
    fax = models.CharField(max_length=150, verbose_name='فکس')
    mobile = models.CharField(max_length=150, verbose_name='موبایل')
    address=models.CharField(max_length=550, verbose_name='آدرس')
    comment=models.CharField(max_length=550, verbose_name='توضیحات')
    # reminbg

    class Meta:
        verbose_name = 'فرد'
        verbose_name_plural = 'افراد'
    def __str__(self):
        return f'{self.name}  {self.lname}'

class WordCount(models.Model):
    word = models.CharField(max_length=100, unique=True, verbose_name='کلمه')  # کلید واژه
    count = models.IntegerField( verbose_name='تعداد')  # تعداد تکرار

    def __str__(self):
        return f"{self.word}: {self.count}"

    class Meta:
        verbose_name = 'تکرار کلمه'
        verbose_name_plural = 'کلمه'



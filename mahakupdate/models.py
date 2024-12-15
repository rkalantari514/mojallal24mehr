from datetime import datetime

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
import jdatetime
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Min
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
    s_m_ratio=models.FloatField(default=0, verbose_name='نسبت فروش به میانگین موجودی')
    last_updated_ratio = models.DateField(blank=True, null=True, verbose_name='آخرین تاریخ به‌روزرسانی')
    # l_mojodi=models.FloatField(default=0, verbose_name='آخرین موجودی')
    # t_sales=models.FloatField(default=0, verbose_name='کل فروش')



    class Meta:
        verbose_name = 'کالا'
        verbose_name_plural = 'کالاها'

    def __str__(self):
        return self.name

    def latest_mojodi(self):
        latest_mojodi = Mojodi.objects.filter(code_kala=self.code).last()
        if latest_mojodi:
            return latest_mojodi.total_stock
        return 0  # در صورتی که هیچ موجودی پیدا نشود، مقدار 0 برگردانده می‌شود

    def total_arzesh(self):
        latest_mojodi = Mojodi.objects.filter(code_kala=self.code).last()
        if latest_mojodi:
            ta = latest_mojodi.total_stock * latest_mojodi.averageprice
            return ta if ta is not None else 0
        return 0


    def total_sales(self):
        end_day = datetime.today()

        # پیدا کردن اولین تاریخ موجود در کاردکس
        start_day = Kardex.objects.aggregate(first_date=Min('date'))['first_date']
        if not start_day:
            return 0  # اگر هیچ کاردکسی وجود نداشت، مقدار 0 برگردانده شود

        total_sales = Kardex.objects.filter(
            code_kala=self.code,
            ktype=1,
            date__range=(start_day, end_day)
        ).aggregate(total=Sum('count'))['total']

        return -1 * total_sales if total_sales is not None else 0

    def last_month_sales(self):
        end_day = datetime.today()
        start_day = end_day - timedelta(days=30)

        total_sales = Kardex.objects.filter(
            code_kala=self.code,
            ktype=1,
            date__range=(start_day, end_day)
        ).aggregate(total=Sum('count'))['total']
        return -1*total_sales if total_sales is not None else 0


    def last_week_sales(self):
        end_day = datetime.today()
        start_day = end_day - timedelta(days=7)

        total_sales = Kardex.objects.filter(
            code_kala=self.code,
            ktype=1,
            date__range=(start_day, end_day)
        ).aggregate(total=Sum('count'))['total']
        return -1*total_sales if total_sales is not None else 0

    def m_sales_mojodi_ratio(self):
        # دریافت فروش ماه گذشته
        ms = self.last_month_sales()

        # محاسبه تاریخ شروع و پایان برای یک ماه گذشته
        end_day = datetime.today()
        start_day = end_day - timedelta(days=30)

        # متغیرها برای نگهداری میانگین موجودی و مجموع موجودی روزانه
        total_stock = 0
        days_count = 0

        # حلقه برای هر روز در بازه زمانی یک ماه گذشته
        for single_date in (start_day + timedelta(n) for n in range(30)):
            # دریافت آخرین کاردکس روز
            kardex = Kardex.objects.filter(
                code_kala=self.code,
                date=single_date
            ).order_by('-date').first()

            if kardex:
                total_stock += kardex.stock
                days_count += 1
            else:
                # استفاده از آخرین موجودی قبلی اگر برای آن روز کاردکس وجود نداشت
                last_kardex = Kardex.objects.filter(
                    code_kala=self.code,
                    date__lt=single_date
                ).order_by('-date').first()
                if last_kardex:
                    total_stock += last_kardex.stock
                    days_count += 1

        # محاسبه میانگین موجودی
        ave_mojodi = total_stock / days_count if days_count > 0 else 0

        # محاسبه نسبت فروش به میانگین موجودی ماهانه
        if ave_mojodi == 0:
            return 0

        mr = ms / ave_mojodi
        return mr


    def sales_mojodi_ratio(self):
        # دریافت مجموع فروش از ابتدای دوره تا حال
        ms = self.total_sales()

        # محاسبه تاریخ شروع از اولین تاریخ موجود در کاردکس
        first_kardex_date = Kardex.objects.aggregate(first_date=Min('date'))['first_date']
        if not first_kardex_date:
            return 0  # اگر کاردکسی وجود نداشت، مقدار 0 برگردانده شود

        # تبدیل first_kardex_date به datetime
        start_day = datetime.combine(first_kardex_date, datetime.min.time())
        end_day = datetime.now()

        # متغیرها برای نگهداری میانگین موجودی و مجموع موجودی روزانه
        total_stock = 0
        days_count = 0

        # حلقه برای هر روز در بازه زمانی از اولین تاریخ تا اکنون
        for single_date in (start_day + timedelta(n) for n in range((end_day - start_day).days + 1)):
            # دریافت آخرین کاردکس روز
            kardex = Kardex.objects.filter(
                code_kala=self.code,
                date=single_date.date()
            ).order_by('-date').first()

            if kardex:
                total_stock += kardex.stock
                days_count += 1
            else:
                # استفاده از آخرین موجودی قبلی اگر برای آن روز کاردکس وجود نداشت
                last_kardex = Kardex.objects.filter(
                    code_kala=self.code,
                    date__lt=single_date.date()
                ).order_by('-date').first()
                if last_kardex:
                    total_stock += last_kardex.stock
                    days_count += 1

        # محاسبه میانگین موجودی
        ave_mojodi = total_stock / days_count if days_count > 0 else 0

        # محاسبه نسبت فروش به میانگین موجودی
        if ave_mojodi == 0:
            return 0

        mr = ms / ave_mojodi
        return mr

    def related_kalas(self):
        current_kala = Kala.objects.filter(code=self.code).last()
        if not current_kala:
            return Kala.objects.none()

        # پیدا کردن کالاهای هم‌گروه
        related_kalas = Kala.objects.filter(category=current_kala.category)

        # فیلتر کردن کالاهایی که در کاردکس استفاده شده‌اند
        used_kalas = []
        for kal in related_kalas:
            if Kardex.objects.filter(code_kala=kal.code).exists():
                used_kalas.append(kal)

        return used_kalas

    def related_kardexes(self):
        related_kalas = self.related_kalas()
        related_kardexes = Kardex.objects.filter(code_kala__in=[kala.code for kala in related_kalas]).order_by(
            'date', 'radif')
        return related_kardexes

    def related_mojodis(self):
        related_kalas = self.related_kalas()
        related_mojodis = Mojodi.objects.filter(code_kala__in=[kala.code for kala in related_kalas])
        return related_mojodis


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

class Storagek(models.Model):
    code=models.IntegerField(blank = True,null = True,default=0, verbose_name='کد انبار')
    name = models.CharField(max_length=150,blank = True,null = True,default="-", verbose_name='نام انبار')

    class Meta:
        verbose_name = 'انبار'
        verbose_name_plural = 'انبار ها'

    def __str__(self):
        return self.name




class Kardex(models.Model):
    pdate = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ شمسی')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ میلادی')
    percode = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد شخص')
    ktype = models.IntegerField(blank=True, null=True, default=0, verbose_name='نوع گردش')
    warehousecode = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد انبار')
    storage = models.ForeignKey(Storagek, on_delete=models.SET_NULL, blank=True, null=True)
    mablaghsanad = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ سند')
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    radif = models.IntegerField(blank=True, null=True, default=0, verbose_name='ردیف در فاکتور')  # برای سورت کردن لازم است
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL, blank=True, null=True)
    code_factor = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد فاکتور')
    factor = models.ForeignKey(Factor, on_delete=models.SET_NULL, blank=True, null=True)
    count = models.FloatField(blank=True, null=True, default=0, verbose_name='تعداد')
    averageprice = models.FloatField(blank=True, null=True, default=0, verbose_name='قیمت میانگین')
    stock = models.FloatField(blank=True, null=True, default=0, verbose_name='موجودی')
    is_prioritized = models.BooleanField(default=False)
    sync_mojodi = models.BooleanField(default=False, verbose_name='موجودی سینک شده است؟')

    class Meta:
        verbose_name = 'کاردکس انبار'
        verbose_name_plural = 'کاردکس های انبار'
        ordering = ['-date', '-radif']

    def __str__(self):
        return str(self.pdate)  # تصحیح به str

    def lname(self):
        try:
            person = Person.objects.filter(code=self.percode).first()  # استفاده از filter و first
            if person:
                return person.lname
            else:
                return 'موجودی اول دوره'
        except Person.DoesNotExist:
            return 'موجودی اول دوره'

    def gardesh_type(self):
        types = {
            1: ('فروش','text-success','fa fa-shopping-cart text-success'),
            2: ('خرید','text-primary','fa fa-truck text-primary'),
            3: ('موجودی اول دوره','text-facebook','fa fa-archive text-facebook'),
            6: ('خروج داخلی','text-danger','fa fa-retweet text-danger'),
            7: ('ورود داخلی','text-facebook','fa fa-retweet text-facebook')
        }
        return types.get(self.ktype, ('نامعلوم','text-success','fa fa-question-o'))


class Mojodi(models.Model):
    warehousecode=models.IntegerField(blank = True,null = True,default=0, verbose_name='کد انبار')
    storage = models.ForeignKey(Storagek, on_delete=models.SET_NULL,blank=True, null=True)
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL, null=True, blank=True)
    stock=models.FloatField(blank=True, null=True, default=0, verbose_name='موجودی')
    total_stock=models.FloatField(blank=True, null=True, default=0, verbose_name='کل موجودی ')
    mojodi_roz=models.FloatField(blank=True, null=True, default=0, verbose_name='موجودی روز ')
    averageprice=models.FloatField(blank=True, null=True, default=0, verbose_name='قیمت میانگین')
    arzesh = models.FloatField(blank=True, null=True, default=0, verbose_name='ارزش')

    class Meta:
        verbose_name = 'موجودی کالا'
        verbose_name_plural = 'موجودی کالاها'

    def __str__(self):
        return self.kala.name if self.kala else "کالا نامشخص"


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



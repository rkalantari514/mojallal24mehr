from datetime import datetime

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
import jdatetime
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Min



# Create your models here.

class StaticUpdateTask(models.Model):
    name = models.CharField(max_length=200, verbose_name='نام نمایشی')
    url = models.CharField(max_length=200, unique=True, verbose_name='مسیر URL')
    last_update_time = models.DateTimeField(default=timezone.now, blank=True, null=True, verbose_name='آخرین آپدیت')
    update_duration = models.FloatField(blank=True, null=True, verbose_name='مدت زمان آپدیت (ثانیه)')
    update_priority = models.IntegerField(default=0, verbose_name='اولویت آپدیت')

    class Meta:
        verbose_name = 'وظیفه استاتیک آپدیت'
        verbose_name_plural = 'وظایف استاتیک آپدیت'
        ordering = ['update_priority']

    def __str__(self):
        return f"{self.name} ({self.url})"

class Mtables(models.Model):
    in_use = models.BooleanField(default=False, verbose_name='در حال استفاده است')
    none_use = models.BooleanField(default=False, verbose_name='بدون استفاده')
    schema_name = models.CharField(max_length=150,blank=True,null=True,default='dbo',verbose_name='نام اسکیما',db_index=True)
    name = models.CharField(blank=True, null=True, max_length=150, verbose_name='نام جدول')
    description = models.CharField(blank=True, null=True, max_length=150, verbose_name='توضیح')
    row_count = models.IntegerField(blank=True, null=True, default=0, verbose_name='تعداد ردیف‌ها')
    cloumn_count = models.IntegerField(blank=True, null=True, default=0, verbose_name='تعداد ستون‌ها')  # نگران تایپو نباش
    last_update_time = models.DateTimeField(default=timezone.now, blank=True, null=True, verbose_name='آخرین آپدیت')
    update_period = models.IntegerField(default=60, blank=True, null=True, verbose_name='بازه به‌روزرسانی (دقیقه)')
    update_duration = models.FloatField(blank=True, null=True, verbose_name='مدت زمان به‌روزرسانی (ثانیه)')
    update_priority = models.IntegerField(default=0, blank=True, null=True, verbose_name='اولویت آپدیت')

    class Meta:
        verbose_name = 'جدول محک'
        verbose_name_plural = 'جداول محک'
        ordering = ['update_priority']
        # ✅ اضافه کردن unique_together برای جلوگیری از تکرار
        unique_together = ('schema_name', 'name')  # مهم: جلوگیری از تکرار جدول با همان نام و اسکیما

    def __str__(self):
        if self.schema_name and self.name:
            return f"{self.schema_name}.{self.name}"
        return self.name or "جدول ناشناس"


class KalaGroupinfo(models.Model):
    code = models.IntegerField(default=0, verbose_name='کد اطلاعات گروه بندی')
    code_mahak = models.IntegerField(blank=True, null=True, verbose_name='کد گروه بندی محک')
    cat1 = models.CharField(max_length=150, blank=True, null=True, default="", verbose_name='دسته بندی 1')
    cat2 = models.CharField(max_length=150, blank=True, null=True, default="", verbose_name='دسته بندی 2')
    cat3 = models.CharField(max_length=150, blank=True, null=True, default="", verbose_name='دسته بندی 3')
    contain = models.CharField(max_length=300, blank=True, verbose_name='شامل باشد')
    not_contain = models.CharField(max_length=300, blank=True, verbose_name='شامل نباشد')

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
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='children', null=True, blank=True,
                               verbose_name='دسته‌بندی والد')
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, verbose_name='سطح')
    code_mahak = models.IntegerField(blank=True, null=True, verbose_name='کد گروه بندی محک')
    budget_rate = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True, verbose_name='ضریب بودجه')

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name


class BrandGroupinfo(models.Model):
    code = models.IntegerField(default=0, verbose_name='کد اطلاعات برند یابی')
    brand_name = models.CharField(max_length=150, blank=True, null=True, default="", verbose_name='نام برند')
    brand_img = models.CharField(max_length=150, blank=True, null=True, default="", verbose_name='لوگو برند')
    contain = models.CharField(max_length=300, blank=True, verbose_name='شامل باشد')
    not_contain = models.CharField(max_length=300, blank=True, verbose_name='شامل نباشد')

    class Meta:
        verbose_name = 'شرط برند یابی کالا'
        verbose_name_plural = 'شروط گروه برند یابی کالا'

    def __str__(self):
        return self.contain









class Brand(models.Model):
    name = models.CharField(max_length=150, verbose_name='نام برند')
    logo_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='نام فایل لوگو')

    class Meta:
        verbose_name = 'برند'
        verbose_name_plural = 'برندها'

    def __str__(self):
        return self.name



class Kala(models.Model):
    code = models.IntegerField(default=0, verbose_name='کد کالا')
    grpcode = models.IntegerField(blank=True, null=True, verbose_name='کد گروه کالا در محک')
    name = models.CharField(max_length=150, verbose_name='نام کالا')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='kalas', verbose_name='دسته‌بندی',
                                 blank=True, null=True)
    s_m_ratio = models.FloatField(default=0, verbose_name='نسبت فروش به میانگین موجودی')
    last_updated_ratio = models.DateField(blank=True, null=True, verbose_name='آخرین تاریخ به‌روزرسانی')
    total_sale = models.FloatField(default=0, verbose_name='کل فروش')
    kala_taf=models.IntegerField(blank=True, null=True,default=0, verbose_name='کد تفصیلی کالا')
    brand = models.ForeignKey(Brand,on_delete=models.SET_NULL,related_name='brand_kalas',verbose_name='برند',blank=True,null=True)

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
        return -1 * total_sales if total_sales is not None else 0

    def last_week_sales(self):
        end_day = datetime.today()
        start_day = end_day - timedelta(days=7)

        total_sales = Kardex.objects.filter(
            code_kala=self.code,
            ktype=1,
            date__range=(start_day, end_day)
        ).aggregate(total=Sum('count'))['total']
        return -1 * total_sales if total_sales is not None else 0

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
    acc_year = models.IntegerField(default=1403,verbose_name='سال مالی')
    code = models.IntegerField(blank=True, null=True, default=0, verbose_name='شماره فاکتور')
    pdate = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ شمسی')
    mablagh_factor = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ فاکتور')
    takhfif = models.FloatField(blank=True, null=True, default=0, verbose_name='تخفیف')
    create_time = models.CharField(blank=True, null=True, max_length=150, verbose_name='ساعت ایجاد')
    darsad_takhfif = models.FloatField(blank=True, null=True, default=0, verbose_name='درصد تخفیف')
    darsad_takhfif_end_factor = models.FloatField(blank=True, null=True, default=0, verbose_name='درصد تخفیف پای فاکتور')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ میلادی')
    per_code = models.IntegerField(blank=True, null=True, verbose_name='کد شخص')
    person = models.ForeignKey('Person', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'

    def __str__(self):
        return self.pdate


class FactorDetaile(models.Model):
    acc_year = models.IntegerField(default=1403,verbose_name='سال مالی')
    code_factor = models.IntegerField(blank=True, null=True, default=0, verbose_name='شماره فاکتور')
    radif = models.IntegerField(blank=True, null=True, default=0, verbose_name='ردیف')
    factor = models.ForeignKey(Factor, on_delete=models.SET_NULL, related_name='details', null=True, blank=True)
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL, null=True)
    count = models.FloatField(blank=True, null=True, default=0, verbose_name='تعداد')
    mablagh_vahed = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ واحد')
    mablagh_nahaee = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ نهایی')
    mablagh_after_takhfif_kol = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ نهایی بعد از اعمال تخفیف کل')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ میلادی')

    class Meta:
        verbose_name = 'جزئیات فاکتور'
        verbose_name_plural = 'جزئیات فاکتور ها'

    def __str__(self):
        return str(self.code_factor)  # تصحیح به str



class BackFactor(models.Model):
    acc_year = models.IntegerField(default=1403,verbose_name='سال مالی')
    code = models.IntegerField(blank=True, null=True, default=0, verbose_name='شماره فاکتور برگشتی')
    type = models.IntegerField(blank=True, null=True, default=0, verbose_name='نوع فاکتور برگشتی')
    per_code = models.IntegerField(blank=True, null=True, verbose_name='کد شخص')
    person = models.ForeignKey('Person', on_delete=models.SET_NULL, blank=True, null=True)
    pdate = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ شمسی')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ میلادی')
    sharh = models.CharField(blank=True, null=True, max_length=300, verbose_name='شرح ')
    takhfif = models.FloatField(blank=True, null=True, default=0, verbose_name='تخفیف')


    class Meta:
        verbose_name = 'فاکتور برگشتی'
        verbose_name_plural = 'فاکتورهای برگشتی'

    def __str__(self):
        return f'({self.code}-{self.pdate})'


class BackFactorDetail(models.Model):
    acc_year = models.IntegerField(default=1403,verbose_name='سال مالی')
    code_factor = models.IntegerField(blank=True, null=True, default=0, verbose_name='شماره فاکتور')
    radif = models.IntegerField(blank=True, null=True, default=0, verbose_name='ردیف')
    type = models.IntegerField(blank=True, null=True, default=0, verbose_name='نوع فاکتور برگشتی')
    backfactor = models.ForeignKey(BackFactor, on_delete=models.SET_NULL, related_name='details', null=True, blank=True)
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL, null=True)
    count = models.FloatField(blank=True, null=True, default=0, verbose_name='تعداد')
    naghdi = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ ')

    class Meta:
        verbose_name = 'جزئیات فاکتور برگشتی'
        verbose_name_plural = 'جزئیات فاکتور های برگشتی'

    def __str__(self):
        return str(self.code_factor)  # تصحیح به str





class Storagek(models.Model):
    code = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد انبار')
    name = models.CharField(max_length=150, blank=True, null=True, default="-", verbose_name='نام انبار')

    class Meta:
        verbose_name = 'انبار'
        verbose_name_plural = 'انبار ها'

    def __str__(self):
        return self.name


class Kardex(models.Model):
    acc_year = models.IntegerField(default=1403,verbose_name='سال مالی')
    pdate = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ شمسی')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ میلادی')
    percode = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد شخص')
    ktype = models.IntegerField(blank=True, null=True, default=0, verbose_name='نوع گردش')
    warehousecode = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد انبار')
    storage = models.ForeignKey(Storagek, on_delete=models.SET_NULL, blank=True, null=True)
    mablaghsanad = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ سند')
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    radif = models.IntegerField(blank=True, null=True, default=0,
                                verbose_name='ردیف در فاکتور')  # برای سورت کردن لازم است
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
            1: ('فروش', 'text-success', 'fa fa-shopping-cart text-success'),
            2: ('خرید', 'text-primary', 'fa fa-truck text-primary'),
            3: ('موجودی اول دوره', 'text-facebook', 'fa fa-archive text-facebook'),
            6: ('خروج داخلی', 'text-danger', 'fa fa-retweet text-danger'),
            7: ('ورود داخلی', 'text-facebook', 'fa fa-retweet text-facebook')
        }
        return types.get(self.ktype, ('نامعلوم', 'text-success', 'fa fa-question-o'))


class Mojodi(models.Model):
    warehousecode = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد انبار')
    storage = models.ForeignKey(Storagek, on_delete=models.SET_NULL, blank=True, null=True)
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.FloatField(blank=True, null=True, default=0, verbose_name='موجودی')
    total_stock = models.FloatField(blank=True, null=True, default=0, verbose_name='کل موجودی ')
    mojodi_roz = models.FloatField(blank=True, null=True, default=0, verbose_name='موجودی روز ')
    mojodi_roz_arzesh = models.FloatField(blank=True, null=True, default=0, verbose_name='موجودی روز ارزش')
    averageprice = models.FloatField(blank=True, null=True, default=0, verbose_name='قیمت میانگین')
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
    code = models.IntegerField(default=0, verbose_name='کد گروه')
    name = models.CharField(max_length=150, verbose_name='نام گروه')

    class Meta:
        verbose_name = 'گروه'
        verbose_name_plural = 'گروه ها'

    def __str__(self):
        return self.name

import re



# models.py

class Person(models.Model):
    code = models.IntegerField(default=0, verbose_name='کد فرد', db_index=True)
    grpcode = models.IntegerField(default=0, verbose_name='کد گروه')
    group = models.ForeignKey(PersonGroup, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='گروه')

    prefix = models.CharField(max_length=20, blank=True, null=True, verbose_name='پیشوند نام')  # جدید
    name = models.CharField(max_length=150, blank=True, null=True, verbose_name='نام')
    lname = models.CharField(max_length=150, blank=True, null=True, verbose_name='نام خانوادگی')

    identifier = models.CharField(max_length=150, blank=True, null=True, verbose_name='کد معرف')  # جدید
    comname = models.CharField(max_length=255, blank=True, null=True, verbose_name='نام شرکت / نام معرف')  # جدید

    tel1 = models.CharField(max_length=150, blank=True, null=True, verbose_name='تلفن 1')
    tel2 = models.CharField(max_length=150, blank=True, null=True, verbose_name='تلفن 2')
    fax = models.CharField(max_length=150, blank=True, null=True, verbose_name='فکس')
    mobile = models.CharField(max_length=150, blank=True, null=True, verbose_name='موبایل')

    address = models.CharField(max_length=1000, blank=True, null=True, verbose_name='آدرس')
    address2 = models.CharField(max_length=1000, blank=True, null=True, verbose_name='آدرس 2')
    comment = models.TextField(blank=True, null=True, verbose_name='توضیحات')  # از CharField به TextField

    per_taf = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد تفصیلی فرد')
    clname = models.CharField(max_length=150, blank=True, null=True, verbose_name='نام مخاطب')

    # Timestamps
    created_time = models.CharField(max_length=20, blank=True, null=True, verbose_name='زمان ایجاد')
    created_date = models.CharField(max_length=20, blank=True, null=True, verbose_name='تاریخ ایجاد')
    modified_time = models.CharField(max_length=20, blank=True, null=True, verbose_name='زمان ویرایش')
    modified_date = models.CharField(max_length=20, blank=True, null=True, verbose_name='تاریخ ویرایش')

    class Meta:
        verbose_name = 'فرد'
        verbose_name_plural = 'افراد'
        unique_together = ('code',)  # تضمین یکتایی کد

    def __str__(self):
        return f'{self.full_name()}'

    def full_name(self):
        """نام کامل با پیشوند"""
        prefix = self.prefix or ''
        name = self.name or ''
        lname = self.lname or ''
        full = f"{prefix} {name} {lname}".strip()
        return full if full else f"فرد {self.code}"

    def cleaned_name(self):
        """نام مخاطب بدون کلمات اضافی"""
        full_name = f'{self.name or ""} {self.lname or ""}'.strip()

        if full_name == "رسول غريباني مرزباني استان خراسان رضوي":
            return "رسول غريباني"

        # حذف کلمات و کاراکترهای اضافی
        cleaned = re.split(
            r"[a-zA-Z-$/]|قسط|طرح رفاه\s*\d+ماهه|ماهی\d+|[._+()]", full_name, maxsplit=1
        )[0].strip()
        return cleaned

    def save(self, *args, **kwargs):
        if not self.clname:
            self.clname = self.cleaned_name()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name()

class WordCount(models.Model):
    word = models.CharField(max_length=100, unique=True, verbose_name='کلمه')  # کلید واژه
    count = models.IntegerField(verbose_name='تعداد')  # تعداد تکرار

    def __str__(self):
        return f"{self.word}: {self.count}"

    class Meta:
        verbose_name = 'تکرار کلمه'
        verbose_name_plural = 'کلمه'


class Sanad(models.Model):
    acc_year = models.IntegerField(default=1403,verbose_name='سال مالی')
    code = models.IntegerField(blank=True, null=True, verbose_name='کد')
    tarikh = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ  شمسی')
    sharh = models.CharField(blank=True, null=True, max_length=300, verbose_name='شرح سند')
    sanadid = models.IntegerField(blank=True, null=True, verbose_name='شناسه سند')

    class Meta:
        verbose_name = 'سند'
        verbose_name_plural = 'اسناد'

    def __str__(self):
        return f"{self.code} - {self.tarikh}"


class SanadDetail(models.Model):
    acc_year = models.IntegerField(default=1403,verbose_name='سال مالی')
    code = models.IntegerField(blank=True, null=True, verbose_name='کد')
    tarikh = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ  شمسی')
    date = models.DateField(blank=True, null=True, verbose_name='تاریخ سند')
    radif = models.IntegerField(blank=True, null=True, verbose_name='ردیف')
    kol = models.IntegerField(blank=True, null=True, verbose_name='کل')
    moin = models.IntegerField(blank=True, null=True, verbose_name='معین')
    tafzili = models.IntegerField(blank=True, null=True, verbose_name='تفضیل')
    sharh = models.CharField(max_length=255, null=True, verbose_name='شرح')
    bed = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='بدهکار')
    bes = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='بستانکار')
    sanad_code = models.IntegerField(null=True, verbose_name='کد سند')
    sanad_type = models.IntegerField(null=True, verbose_name='نوع سند')
    meghdar = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مقدار')
    syscomment = models.CharField(max_length=255, null=True, verbose_name='عنوان سند')
    curramount = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مانده')
    usercreated = models.CharField(max_length=255, null=True, verbose_name='ایجاد کننده')
    is_analiz = models.BooleanField(default=False, verbose_name='آنالیز شده است')
    cheque_id = models.CharField(blank=True, null=True, max_length=255,
                                 verbose_name="شناسه چک")  # یا مقدار max_length مناسب
    is_active = models.BooleanField(default=True, verbose_name='فعال است')
    person = models.ForeignKey('Person', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = (('acc_year','code', 'radif'),)  # تعریف کلید یگانه
        verbose_name = 'جزئیات سند'
        verbose_name_plural = 'جزئیات اسناد'

    def __str__(self):
        return f"{self.code}-{self.radif}"

    def kind(self):
        kin = []
        k = self.sharh.split('(')[0].strip()  # جدا کردن متن قبل از اولین پرانتز باز و حذف فاصله‌های اضافی
        if not k:
            k=self.sharh
        kin.append(k)

        # تعریف یک دیکشنری برای شرایط
        conditions = {
            'اول دوره شخص': ['اول دوره', 'primary'],
            'خريدار در فاکتور فروش': ['فروش', 'danger'],
            'مبلغ نقدي در دريافت': ['دریافت', 'success'],
            # 'مبلغ نقدي در دريافت': ['دریافت/نقدی', 'success'],
            # 'حواله دريافتي در دريافت': ['دریافت/حواله', 'success'],
            'حواله دريافتي در دريافت': ['دریافت', 'success'],
            'پرداخت کننده به ازاي چک دريافتي در دريافت': ['دریافت/چک', 'success'],
            'تخفيف فاکتور فروش': ['تخفیف', 'flickr'],
            'شخص بستانکار در حواله حساب': ['برگشت؟', 'flickr'],
            'خريدار در برگشت از فروش': ['برگشت', 'flickr'],
            'بستن حساب هاي دارائي': ['اختتامیه', 'primary']
        }

        # بررسی وجود مقدار در دیکشنری
        if k in conditions:
            kin.extend(conditions[k])  # افزودن مقادیر مرتبط به لیست

        return kin


from django.db import models

class MyCondition(models.Model):
    acc_year = models.IntegerField(default=0, blank=True, null=True, verbose_name='سال مالی')
    kol = models.IntegerField(default=0, blank=True, null=True, verbose_name='کل')
    moin = models.IntegerField(default=0, blank=True, null=True, verbose_name='معین')
    tafzili = models.IntegerField(default=0, blank=True, null=True, verbose_name='تفضیل')

    contain = models.CharField(max_length=255, blank=True, null=True, verbose_name='شامل')
    equal_to = models.CharField(max_length=255, blank=True, null=True, verbose_name='برابر با')
    is_active = models.BooleanField(default=True, verbose_name='فعال است')
    is_new = models.BooleanField(default=True, verbose_name='جدید است')

    def __init__(self, *args, **kwargs):
        super(MyCondition, self).__init__(*args, **kwargs)
        # ذخیره مقادیر اولیه فیلدها
        self._original_values = {
            'kol': self.kol,
            'moin': self.moin,
            'tafzili': self.tafzili,
            'contain': self.contain,
            'equal_to': self.equal_to,
            'is_active': self.is_active,
            'is_new': self.is_new,
        }

    def save(self, *args, **kwargs):
        # بررسی تغییرات در فیلدهای غیر از is_new
        if any(
            getattr(self, field) != self._original_values[field]
            for field in ['kol', 'moin', 'tafzili', 'contain', 'equal_to', 'is_active']
        ):
            self.is_new = True  # اگر فیلدهای دیگر تغییر کردند، is_new را True کنید
        elif self.is_new != self._original_values['is_new'] and not self.is_new:
            # اگر فقط is_new تغییر کرد و به False تنظیم شد، آن را False نگه دارید
            self.is_new = False

        # ذخیره شیء
        super(MyCondition, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'شرط استثنا'
        verbose_name_plural = 'شرایط استثنا'

    def __str__(self):
        return f"شرط: kol={self.kol}, moin={self.moin}, tafzili={self.tafzili}"


from django.db import models

from django.db import models


class AccCoding(models.Model):
    LEVEL_CHOICES = (
        (1, 'کل'),  # Klo
        (2, 'معین'),  # Moin
        (3, 'تفضیلی'),  # Tafsili
    )
    code = models.IntegerField(verbose_name='کد')  # کد دسته‌بندی
    name = models.CharField(max_length=150, verbose_name='نام دسته‌بندی')
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, verbose_name='سطح')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children',
                               verbose_name='پدر')
    is_budget = models.BooleanField(default=False, verbose_name='بودجه است؟')
    budget_rate = models.FloatField(blank=True, null=True, verbose_name='ضریب بودجه')

    class Meta:
        verbose_name = 'کدینگ حسابداری'
        verbose_name_plural = 'کدینگ های حسابداری'
        # unique_together = ('code', 'level', 'parent')  # کد، سطح و والد باید یکتا باشند

    def __str__(self):
        return f"{self.code} - {self.name} (سطح {self.level})"


#
class ChequesRecieve(models.Model):
    id_mahak = models.AutoField(primary_key=True, verbose_name="شناسه")
    # cheque_id = models.IntegerField(verbose_name="شناسه چک")
    cheque_id = models.CharField(max_length=255, verbose_name="شناسه چک")  # یا مقدار max_length مناسب
    cheque_row = models.IntegerField(verbose_name="ردیف چک")
    issuance_tarik = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ صدور شمسی')
    issuance_date = models.DateField(verbose_name="تاریخ صدور میلادی")
    cheque_tarik = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ چک شمسی')
    cheque_date = models.DateField(verbose_name="تاریخ چک میلادی")
    cost = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="مبلغ")
    bank_name = models.CharField(max_length=255, verbose_name="نام بانک")
    bank_logo=models.CharField(blank=True, null=True,max_length=255, verbose_name="نام لگو بانک")
    bank_branch = models.CharField(max_length=255, verbose_name="شعبه بانک")
    account_id = models.IntegerField(verbose_name="شناسه حساب")
    description = models.TextField(verbose_name="توضیحات")
    status = models.CharField(max_length=50, verbose_name="وضعیت")
    per_code = models.CharField(max_length=50, verbose_name="کد شخص")
    total_mandeh = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مانده کل چک')
    last_sanad_detaile = models.ForeignKey(SanadDetail, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'چک دریافتی'
        verbose_name_plural = 'چکهای دریافتی'

    def sanad_detail(self):
        sd = SanadDetail.objects.filter(cheque_id=self.cheque_id,kol=101).order_by('date', 'code', 'radif').last()
        return sd

    from django.db.models import Sum, F

    def mandeh(self):
        # اگر می خواهید از cache استفاده کنید، می توانید از cache استفاده کنید.
        totals = SanadDetail.objects.filter(cheque_id=self.cheque_id,kol=101).aggregate(
            total_bes=Sum('bes'),
            total_bed=Sum('bed')
        )
        return (totals['total_bes'] or 0) - (totals['total_bed'] or 0)
    def person(self):
        try:
            name = Person.objects.filter(code=self.per_code).last().name
            family = Person.objects.filter(code=self.per_code).last().lname
            return f'{name} {family}'
        except:
            return '---'


class Bank(models.Model):

    code = models.IntegerField(blank=True, null=True,verbose_name="کد بانک")
    name = models.CharField(blank=True, null=True,max_length=255, verbose_name="نام بانک")
    bank_name=models.CharField(blank=True, null=True,max_length=255, verbose_name="نام بانک اصلی")
    bank_logo=models.CharField(blank=True, null=True,max_length=255, verbose_name="نام لگو بانک")
    shobe = models.CharField(blank=True, null=True,max_length=255, verbose_name="نام شعبه")
    sh_h = models.CharField(blank=True, null=True,max_length=255, verbose_name="شماره حساب")
    type_h = models.CharField(blank=True, null=True,max_length=255, verbose_name="نوع حساب")
    mogodi=models.DecimalField(blank=True, null=True,max_digits=14, decimal_places=2, verbose_name="موجودی")
    firstamount=models.DecimalField(blank=True, null=True,max_digits=14, decimal_places=2, verbose_name="موجودی اول دوره")

    class Meta:
        verbose_name = 'بانک'
        verbose_name_plural = 'بانک ها'

    def __str__(self):
        return f"{self.bank_name} - {self.name}"



class ChequesPay(models.Model):
    id_mahak = models.AutoField(primary_key=True, verbose_name="شناسه")
    cheque_id = models.CharField(max_length=255, verbose_name="شناسه چک")  # یا مقدار max_length مناسب
    cheque_row = models.IntegerField(verbose_name="ردیف چک")
    issuance_tarik = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ صدور شمسی')
    issuance_date = models.DateField(verbose_name="تاریخ صدور میلادی")
    cheque_tarik = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ چک شمسی')
    cheque_date = models.DateField(verbose_name="تاریخ چک میلادی")
    cost = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="مبلغ")
    bank_code = models.IntegerField(verbose_name="کد بانک")
    bank=models.ForeignKey(Bank,on_delete=models.SET_NULL, blank=True, null=True)
    description = models.TextField(verbose_name="توضیحات")
    status = models.CharField(max_length=50, verbose_name="وضعیت")
    firstperiod=models.BooleanField(verbose_name='چک اول دوره')
    cheque_id_counter=models.IntegerField(verbose_name="تعداد آی دی چک")
    per_code = models.CharField(max_length=50, verbose_name="کد شخص")
    person=models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True)
    recieve_status=models.IntegerField(verbose_name="وضعیت دریافت")
    total_mandeh = models.DecimalField(max_digits=30, decimal_places=10, null=True, verbose_name='مانده کل چک')
    last_sanad_detaile = models.ForeignKey(SanadDetail, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'چک پرداختی'
        verbose_name_plural = 'چکهای پرداختی'

    def sanad_detail(self):
        sd = SanadDetail.objects.filter(cheque_id=self.cheque_id,kol=200).order_by('date', 'code', 'radif').last()
        return sd

    from django.db.models import Sum, F

    def mandeh(self):
        # اگر می خواهید از cache استفاده کنید، می توانید از cache استفاده کنید.
        totals = SanadDetail.objects.filter(cheque_id=self.cheque_id,kol=200).aggregate(
            total_bes=Sum('bes'),
            total_bed=Sum('bed')
        )
        return (totals['total_bes'] or 0) - (totals['total_bed'] or 0)




class Loan(models.Model):
    code = models.IntegerField(blank=True, null=True, verbose_name='کد')
    name_code = models.IntegerField(blank=True, null=True, verbose_name='کد نام')
    person=models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True)
    tarikh = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ  شمسی')
    date = models.DateField(blank=True, null=True,verbose_name="تاریخ میلادی")
    number = models.IntegerField(blank=True, null=True, verbose_name='تعداد اقساط')
    distance = models.IntegerField(blank=True, null=True, verbose_name='فاصله اقساط')
    cost = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="مبلغ")
    loan_mandeh = models.DecimalField(default=0,max_digits=14, decimal_places=2, verbose_name="مانده قسط")
    actual_loan_mandeh = models.DecimalField(default=0,max_digits=14, decimal_places=2, verbose_name="مانده قسط واقعی")
    delayed_loan = models.DecimalField(default=0,max_digits=14, decimal_places=2, verbose_name="مانده قسط معوق")


    class Meta:
        verbose_name = 'قسط'
        verbose_name_plural = 'قسط ها'

    def __str__(self):
        return f"{self.code}"

    def tasfiiye(self):
        tas=self.cost-self.loan_mandeh
        return tas


class LoanDetil(models.Model):
    code = models.IntegerField(blank=True, null=True, verbose_name='کد')
    loan_code = models.IntegerField(blank=True, null=True, verbose_name='کد وام')
    loan=models.ForeignKey(Loan, on_delete=models.SET_NULL, blank=True, null=True)
    row = models.IntegerField(blank=True, null=True, verbose_name='ردیف')
    tarikh = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ  شمسی')
    date = models.DateField(blank=True, null=True,verbose_name="تاریخ میلادی")
    recive_tarikh = models.CharField(blank=True, null=True, max_length=150, verbose_name='تاریخ  دریافت شمسی')
    recive_date = models.DateField(blank=True, null=True,verbose_name="تاریخ دریافت میلادی")
    delay = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="تاخیر")
    cost = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="مبلغ")
    comment=models.CharField(blank=True, null=True, max_length=250, verbose_name='توضیح')
    complete_percent  = models.FloatField(default=0.0, verbose_name='درصد تکمیل قسط')

    class Meta:
        verbose_name = 'جزئیات وام'
        verbose_name_plural = 'جزئیات وام ها'

    def __str__(self):
        return f"{self.code} - {self.tarikh}"


    def last_tracks(self):
        from loantracker.models import Tracking
        return Tracking.objects.filter(customer__person=self.loan.person).last() or None




class GoodConsign(models.Model):
    code = models.IntegerField(unique=True, verbose_name='کد حواله')
    per_code = models.IntegerField(blank=True, null=True, verbose_name='کد فرد')
    person = models.ForeignKey('Person', on_delete=models.SET_NULL, blank=True, null=True)
    good_code = models.IntegerField(blank=True, null=True, verbose_name='کد کالا')
    kala = models.ForeignKey(Kala, on_delete=models.SET_NULL, null=True, blank=True)
    store_code = models.IntegerField(blank=True, null=True, verbose_name='کد انبار')
    storage =  models.ForeignKey(Storagek, on_delete=models.SET_NULL, null=True, blank=True)
    p_date = models.CharField(max_length=20, blank=True, null=True, verbose_name='تاریخ  شمسی')
    date = models.DateField(blank=True, null=True,verbose_name="تاریخ میلادی")
    p_return_date = models.CharField(max_length=20, blank=True, null=True, verbose_name='تاریخ شمسی بازگشت')
    return_date = models.DateField(blank=True, null=True,verbose_name="تاریخ برگشت میلادی")
    amount1 = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, verbose_name='مقدار۱')
    operation_type = models.IntegerField(blank=True, null=True, verbose_name='نوع عملیات')
    comment = models.CharField(max_length=550, blank=True, null=True, verbose_name='توضیحات')
    owner_consign_code = models.IntegerField(blank=True, null=True, verbose_name='کد مالک حواله')

    class Meta:
        verbose_name = 'کالای امانی'
        verbose_name_plural = 'کالاهای امانی'

    def __str__(self):
        return f"حواله {self.code}"

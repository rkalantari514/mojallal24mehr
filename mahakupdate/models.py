from django.db import models

# Create your models here.


class Mtables(models.Model):
    in_use = models.BooleanField(default=False, verbose_name='در حال استفاده است')
    none_use = models.BooleanField(default=False, verbose_name=' بدون استفاده')
    name = models.CharField(blank = True,null = True,max_length=150, verbose_name='نام جدول')
    description = models.CharField(blank = True,null = True,max_length=150, verbose_name='توضیح')
    row_count = models.IntegerField(blank = True,null = True,default=0, verbose_name='تعداد ردیف ها')
    cloumn_count = models.IntegerField(blank = True,null = True,default=0, verbose_name='تعداد ستون ها')

    class Meta:
        verbose_name = 'جدول محک'
        verbose_name_plural = 'جداول محک'
    def __str__(self):
        return self.name


class Category(models.Model):
    LEVEL_CHOICES = (
        (1, 'سطح 1'),
        (2, 'سطح 2'),
        (3, 'سطح 3'),
    )
    name = models.CharField(max_length=150, verbose_name='نام دسته‌بندی')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True, verbose_name='دسته‌بندی والد')
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, verbose_name='سطح')

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name



class Kala(models.Model):
    code= models.IntegerField(default=0, verbose_name='کد کالا')
    name = models.CharField(max_length=150, verbose_name='نام کالا')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='kalas', verbose_name='دسته‌بندی',blank = True,null = True)


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




    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'

    def __str__(self):
        return self.pdate


class FactorDetaile(models.Model):
    code_factor = models.IntegerField(blank=True, null=True, default=0, verbose_name='شماره فاکتور')
    radif= models.IntegerField(blank = True,null = True,default=0, verbose_name='ردیف')
    factor = models.ForeignKey(Factor, on_delete=models.CASCADE, related_name='details', null=True, blank = True)
    code_kala = models.IntegerField(blank=True, null=True, default=0, verbose_name='کد کالا')
    kala = models.ForeignKey(Kala, on_delete=models.CASCADE, null=True)
    count = models.FloatField(blank=True, null=True, default=0, verbose_name='تعداد')
    mablagh_vahed = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ واحد')
    mablagh_nahaee = models.FloatField(blank=True, null=True, default=0, verbose_name='مبلغ نهایی')

    class Meta:
        verbose_name = 'جزئیات فاکتور'
        verbose_name_plural = 'جزئیات فاکتور ها'

    def __str__(self):
        return str(self.code_factor)  # تصحیح به str


class WordCount(models.Model):
    word = models.CharField(max_length=100, unique=True, verbose_name='کلمه')  # کلید واژه
    count = models.IntegerField( verbose_name='تعداد')  # تعداد تکرار

    def __str__(self):
        return f"{self.word}: {self.count}"

    class Meta:
        verbose_name = 'تکرار کلمه'
        verbose_name_plural = 'کلمه'



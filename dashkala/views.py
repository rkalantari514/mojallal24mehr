from django.shortcuts import render
from django.db.models import Subquery, OuterRef
from mahakupdate.models import Kardex
from persianutils import standardize

def fix_persian_characters(value):
    return standardize(value)


# Create your views here.
def DsshKala (request):

    for kala in Kardex.objects.all():
        print(kala.code_kala,kala.kala.name,kala.warehousecode,kala.stock)

    # زیر پرس‌وجو برای دریافت آخرین ردیف از هر `code_kala`
    subquery = Kardex.objects.filter(
        code_kala=OuterRef('code_kala'),warehousecode=OuterRef('warehousecode')
    ).values('id')[:1]
    # دریافت آخرین ردیف از هر `code_kala`
    mojodi = Kardex.objects.filter(id__in=Subquery(subquery))

    # نمایش نتایج
    for entry in mojodi:
        entry.kala.name = fix_persian_characters(entry.kala.name)

        # pass
        print(entry.pdate,entry.code_kala, entry.stock ,entry.kala.name)

    context= {
        'title': 'داشبورد کالاها',
        'mojodi':mojodi,
    }
    return render(request, 'dash_kala.html', context)

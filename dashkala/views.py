from django.shortcuts import render
from django.db.models import Subquery, OuterRef
from mahakupdate.models import Kardex, Mtables
from persianutils import standardize
from django.utils import timezone

def fix_persian_characters(value):
    return standardize(value)


# Create your views here.
def DsshKala (request):
    # زیر پرس‌وجو برای دریافت آخرین ردیف از هر `code_kala`
    subquery = Kardex.objects.filter(
        code_kala=OuterRef('code_kala'),warehousecode=OuterRef('warehousecode')
    ).values('id')[:1]
    # دریافت آخرین ردیف از هر `code_kala`
    mojodi = Kardex.objects.filter(id__in=Subquery(subquery))

    # نمایش نتایج
    for entry in mojodi:
        entry.kala.name = fix_persian_characters(entry.kala.name)
        entry.arzesh=entry.stock*entry.averageprice

        # pass
        print(entry.pdate,entry.code_kala, entry.stock ,entry.kala.name)

    table=Mtables.objects.filter(name='Kardex').last()

    tsinse = (timezone.now() - table.last_update_time).total_seconds() / 60
    if tsinse / table.update_period >= 1:
        table.progress_bar_width = 100
        table.progress_class = 'skill2-bar bg-danger'
    elif tsinse / table.update_period < 0.4:
        table.progress_class = 'skill2-bar bg-success'
        table.progress_bar_width = tsinse / table.update_period * 100
    elif tsinse / table.update_period < 0.9:
        table.progress_bar_width = tsinse / table.update_period * 100
        table.progress_class = 'skill2-bar bg-warning'
    elif tsinse / table.update_period < 1:
        table.progress_bar_width = tsinse / table.update_period * 100
        table.progress_class = 'skill2-bar bg-danger'

    top_5_arzesh = sorted(mojodi, key=lambda x: x.arzesh, reverse=True)[:5]

    for entry in top_5_arzesh:
        print(entry.kala.name,entry.arzesh)

    total_arzesh = sum([item.arzesh for item in top_5_arzesh])

    current_start = 0
    for item in top_5_arzesh:
        item.start = current_start
        item.end = current_start + item.arzesh / total_arzesh
        current_start = item.end

    context= {
        'title': 'داشبورد کالاها',
        'mojodi':mojodi,
        'table':table,
        'top_5_arzesh':top_5_arzesh,
    }
    return render(request, 'dash_kala.html', context)

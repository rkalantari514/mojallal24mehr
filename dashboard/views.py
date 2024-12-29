from django.shortcuts import render

from mahakupdate.models import Factor, FactorDetaile
from django.db.models import Sum
from django.contrib.auth.decorators import login_required


# Create your views here.



@login_required(login_url='/login')
def Home1(request):
    user=request.user

    factor=Factor.objects.all()
    mablagh_factor_total = factor.aggregate(Sum('mablagh_factor'))['mablagh_factor__sum']
    count_factor_total = factor.count()





    factor_detile=FactorDetaile.objects.all()
    count_factor_detile = factor_detile.count()







    for i in factor_detile:
        print(i.kala.name)
    print('i.kala=====================================================================.name')




    yakhfa = FactorDetaile.objects.filter(kala__name__contains='يخچال')
    mablagh_yakh=yakhfa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    yakhdarsad = mablagh_yakh /mablagh_factor_total*100

    lebafa = FactorDetaile.objects.filter(kala__name__contains='لباسشويي')
    mablagh_leba = lebafa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    lebadarsad = mablagh_leba / mablagh_factor_total * 100


    colfa = FactorDetaile.objects.filter(kala__name__contains='کولر')
    mablagh_col = colfa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    coldarsad = mablagh_col / mablagh_factor_total * 100





    print(mablagh_factor_total)

    context = {

        'factor': factor,
        'user': user,
        'mablagh_factor_total':mablagh_factor_total,
        'count_factor_total':count_factor_total,
        'factor_detile':factor_detile,
        'mablagh_yakh':mablagh_yakh,
        'yakhdarsad':yakhdarsad,


        'mablagh_leba':mablagh_leba,
        'lebadarsad':lebadarsad,


        'mablagh_col':mablagh_col,
        'coldarsad':coldarsad,
    }



    return render(request, 'homepage.html',context)
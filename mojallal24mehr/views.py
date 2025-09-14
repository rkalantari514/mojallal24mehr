import sys

from django.shortcuts import render

from custom_login.models import MyPage
from dashboard.models import MasterInfo
from mahakupdate.models import Category
from django.contrib.auth.decorators import login_required


def get_category_tree(parent=None):
    categories = Category.objects.filter(parent=parent).order_by('id')
    tree = []
    for category in categories:
        subtree = get_category_tree(category)
        tree.append({
            'id': category.id,
            'name': category.name,
            'children': subtree
        })
    return tree

# for render partial
def header(request, *args, **kwargs):
    sys.stdout.reconfigure(encoding='utf-8')  # اضافه کنید قبل از print
    user=request.user
    last_update_time = MasterInfo.objects.filter(is_active=True).last().last_update_time
    context = {
        'user':user,
        'last_update_time':last_update_time,
    }
    return render(request, 'shared/Header.html', context)

# def sidebar(request, *args, **kwargs):
#     category_tree = get_category_tree()
#     user = request.user
#     last_update_time = MasterInfo.objects.filter(is_active=True).last().last_update_time
#
#     context = {
#         'is_dark_mode': user.is_dark_mode,
#         'category_tree': category_tree,
#         'last_update_time': last_update_time,
#
#     }
#     return render(request, 'shared/Sidebar.html', context)
from django.shortcuts import render

def sidebar(request, *args, **kwargs):
    # گرفتن کاربر
    user = request.user
    is_superuser=user.is_superuser
    if user.is_superuser:
        allowed_pages = MyPage.objects.all().distinct()
    else:
        allowed_pages = MyPage.objects.filter(allowed_groups__user=user).distinct()

    # گرفتن لیست صفحات مجاز

    # تبدیل به یک لیست ساده از URLها
    allowed_view = allowed_pages.values_list('v_name', flat=True)
    print('allowed_view',allowed_view)
    # سایر داده‌ها
    category_tree = get_category_tree()
    last_update_time = MasterInfo.objects.filter(is_active=True).last().last_update_time
    years=[1403,1404]


    context = {
        'years': years,
        'is_dark_mode': user.is_dark_mode,
        'category_tree': category_tree,
        'last_update_time': last_update_time,
        'allowed_view': allowed_view,  # ارسال لیست لینک‌های مجاز به قالب
        'is_superuser': is_superuser,  # ارسال لیست لینک‌های مجاز به قالب
    }
    return render(request, 'shared/Sidebar.html', context)


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
@login_required
def update_dark_mode(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request.user.is_dark_mode = data.get('is_dark_mode', False)
        request.user.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'}, status=400)






def footer(request, *args, **kwargs):
    context = {
    }
    return render(request, 'shared/Footer.html', context)

def handle_404_error(request, exception):

    return render(request, '404.html', {})

def handle_500_error(request, exception):

    return render(request, '404.html', {})




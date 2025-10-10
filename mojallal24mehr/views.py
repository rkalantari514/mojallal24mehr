import sys

from django.shortcuts import render
from django.http import FileResponse, Http404
import mimetypes
import os
from django.utils._os import safe_join

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
    # Ensure stdout is UTF-8 where supported, but don’t crash if not (e.g., IIS wfastcgi)
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    user = request.user
    last_info = MasterInfo.objects.filter(is_active=True).last()
    last_update_time = getattr(last_info, 'last_update_time', None)
    context = {
        'user': user,
        'last_update_time': last_update_time,
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
    return render(request, '404.html', status=404)

def handle_500_error(request):
    # You can create a dedicated 500.html template; for now reuse 404 layout textually
    return render(request, '404.html', status=500)


def dev_static(request, path, root):
    """
    Lightweight static file server for local DEBUG=False testing.
    Serves files from the given root safely, returns 404 if not found.
    """
    try:
        fullpath = safe_join(root, path)
    except Exception:
        raise Http404

    if not os.path.exists(fullpath) or not os.path.isfile(fullpath):
        raise Http404

    content_type, _ = mimetypes.guess_type(fullpath)
    # Fallback MIME types on Windows if not detected
    if not content_type:
        if fullpath.endswith('.css'):
            content_type = 'text/css'
        elif fullpath.endswith('.js'):
            content_type = 'application/javascript'
    try:
        return FileResponse(open(fullpath, 'rb'), content_type=content_type or 'application/octet-stream')
    except Exception:
        # Avoid leaking server errors via static requests; treat as not found
        raise Http404




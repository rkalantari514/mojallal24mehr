from django.shortcuts import render

from mahakupdate.models import Category
from django.contrib.auth.decorators import login_required


def get_category_tree(parent=None):
    categories = Category.objects.filter(parent=parent).order_by('-id')
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
    user=request.user
    context = {
        'user':user,
    }
    return render(request, 'shared/Header.html', context)

def sidebar(request, *args, **kwargs):
    category_tree = get_category_tree()
    user = request.user
    context = {
        'is_dark_mode': user.is_dark_mode,
        'category_tree': category_tree,
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




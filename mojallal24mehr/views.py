from django.shortcuts import render

from mahakupdate.models import Category


def get_category_tree(parent=None):
    categories = Category.objects.filter(parent=parent)
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
    return render(request, 'shared/Sidebar.html', {'category_tree': category_tree})

def footer(request, *args, **kwargs):
    context = {
    }
    return render(request, 'shared/Footer.html', context)

def handle_404_error(request, exception):

    return render(request, '404.html', {})

def handle_500_error(request, exception):

    return render(request, '404.html', {})




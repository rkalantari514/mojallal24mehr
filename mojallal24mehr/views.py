from django.shortcuts import render


# for render partial
def header(request, *args, **kwargs):
    user=request.user
    context = {
        'user':user,
    }
    return render(request, 'shared/Header.html', context)

def sidebar(request, *args, **kwargs):

    return render(request, 'shared/Sidebar.html')

def footer(request, *args, **kwargs):
    context = {
    }
    return render(request, 'shared/Footer.html', context)

def handle_404_error(request, exception):

    return render(request, '404.html', {})

def handle_500_error(request, exception):

    return render(request, '404.html', {})




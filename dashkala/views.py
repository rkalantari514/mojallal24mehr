from django.shortcuts import render

# Create your views here.
def DsshKala (request):
    context= {
        'title': 'داشبورد کالاها',
    }
    return render(request, 'dash_kala.html', context)

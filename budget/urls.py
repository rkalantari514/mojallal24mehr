from django.urls import path

from budget.views import BudgetTotal

urlpatterns = [

    path('budget/total', BudgetTotal, name='budget_total'),

]

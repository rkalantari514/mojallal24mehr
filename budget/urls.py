from django.urls import path

from budget.views import BudgetCostTotal, BudgetCostDetail

urlpatterns = [

    path('budget/cost/total', BudgetCostTotal, name='budget_cost_total'),
    path('budget/cost/detail/<level>/<code>', BudgetCostDetail, name='budget_cost_detail'),

]

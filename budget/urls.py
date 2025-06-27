from django.urls import path

from budget.views import BudgetCostTotal, BudgetCostDetail, BudgetSaleTotal, BudgetSaleDetail

urlpatterns = [

    path('budget/cost/total', BudgetCostTotal, name='budget_cost_total'),
    path('budget/sale/total', BudgetSaleTotal, name='budget_sale_total'),
    path('budget/cost/detail/<level>/<code>', BudgetCostDetail, name='budget_cost_detail'),


    path('budget/sale/detail/<level>/<code>', BudgetSaleDetail, name='budget_sale_detail'),

]

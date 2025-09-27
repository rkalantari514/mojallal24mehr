from django.urls import path

from budget.views import BudgetCostTotal, BudgetCostDetail, BudgetSaleTotal, BudgetSaleDetail, BudgetSaleFactorDetail, \
    BudgetTotal, BudgetSaleQtyTotal, BudgetSaleQtyDetail, BudgetSaleBackFactorDetail

urlpatterns = [

    path('budget/total', BudgetTotal, name='budget_total'),
    path('budget/cost/total', BudgetCostTotal, name='budget_cost_total'),
    path('budget/sale/total', BudgetSaleTotal, name='budget_sale_total'),
    path('budget/cost/detail/<level>/<code>', BudgetCostDetail, name='budget_cost_detail'),


    path('budget/sale/detail/<level>/<code>', BudgetSaleDetail, name='budget_sale_detail'),



    path('budget/sale/factor/<year>/<level>/<code>', BudgetSaleFactorDetail, name='budget_sale_factor_detail'),


# --- Quantity-based budget views ---
    path('budget/sale/qty/total', BudgetSaleQtyTotal, name='budget_sale_qty_total'),
    path('budget/sale/qty/detail/<level>/<code>', BudgetSaleQtyDetail, name='budget_sale_qty_detail'),
    path('budget/sale/backfactor/<year>/<level>/<code>', BudgetSaleBackFactorDetail, name='budget_sale_back_factor_detail'),


]

from django.contrib import admin
from django.contrib import admin
from .models import MasterReport
from dashboard.models import MasterInfo


# Register your models here.
class MasterInfoAdmin(admin.ModelAdmin):
    list_display = ['acc_year','company_name','is_active']
    list_editable = ['company_name','is_active']

    class Meta:
        model = MasterInfo




@admin.register(MasterReport)
class MasterReportAdmin(admin.ModelAdmin):
    list_display = ('day', 'total_mojodi', 'value_of_purchased_goods', 'cost_of_sold_goods', 'revenue_from_sales')
    search_fields = ('day',)
    list_filter = ('day',)


admin.site.register(MasterInfo, MasterInfoAdmin)
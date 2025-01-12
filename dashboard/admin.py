from django.contrib import admin

from dashboard.models import MasterInfo


# Register your models here.
class MasterInfoAdmin(admin.ModelAdmin):
    list_display = ['acc_year','company_name','is_active']
    list_editable = ['company_name','is_active']

    class Meta:
        model = MasterInfo



admin.site.register(MasterInfo, MasterInfoAdmin)
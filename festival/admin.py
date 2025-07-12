from django.contrib import admin
from .models import Festival, CustomerPoints


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'min_invoice_amount', 'points_per_purchase_ratio', 'is_active')
    search_fields = ('name',)
    ordering = ('-start_date',)




@admin.register(CustomerPoints)
class CustomerPointsAdmin(admin.ModelAdmin):
    list_display = ('festival', 'customer', 'phone_number','factor','factor__code', 'points_awarded', 'award_date','pin_code','is_win','is_send_pin','message_id_pin')
    list_filter = ('festival', 'award_date')
    search_fields = ('customer__name', 'customer__lname', 'factor__code', 'festival__name')
    ordering = ('-award_date',)
    list_editable = ['is_win']
    # می‌توانید فارنکی‌ها را به صورت raw_id_fields نمایش دهید اگر تعداد زیادی رکورد دارید
    # raw_id_fields = ('festival', 'customer', 'factor')
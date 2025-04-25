from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import TrackKinde, Tracking


@admin.register(TrackKinde)
class TrackKindeAdmin(admin.ModelAdmin):
    list_display = ('kind_name', 'kind_icon', 'kind_color')
    search_fields = ('kind_name',)



from django.contrib import admin
from .models import Tracking


@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'created_by',
        'customer',
        'track_kind',
        'next_reminder_date',
        'call_duration'
    )
    search_fields = ('customer__person', 'track_kind__kind_name',)
    list_filter = ('created_at', 'track_kind', 'customer',)

    # اضافه کردن فیلدهای فقط خواندنی
    readonly_fields = ('created_at',)



from django.contrib import admin
from .models import SampleSMS

@admin.register(SampleSMS)
class SampleSMSAdmin(admin.ModelAdmin):
    list_display = ('text', 'level')  # نمایش متن پیامک و سطح پیامک



from django.urls import path

from festival.views import Calculate_and_award_points, FestivalTotal, send_bulk_promotional_sms, FestivalPinSms, \
    FestivalSmsStatusUpdate

urlpatterns = [

    path('update/calculate_award', Calculate_and_award_points, name="calculate-award_points"),
    path('update/send-festival-sms', send_bulk_promotional_sms, name="send_festival_sms"),

    path('festival_total', FestivalTotal, name="festival-total"),

    path('festival/pinsms/<festival_id>', FestivalPinSms, name="festival-pin-sms"),
    path('festival/update/sms_status/<festival_id>', FestivalSmsStatusUpdate, name="festival_sms_status_update"),

]



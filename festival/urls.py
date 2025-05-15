




from django.urls import path

from festival.views import Calculate_and_award_points, FestivalTotal

urlpatterns = [

    path('update/calculate_award', Calculate_and_award_points, name="calculate-award_points"),



    path('festival_total', FestivalTotal, name="festival-total"),


]



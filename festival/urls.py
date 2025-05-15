




from django.urls import path

from festival.views import Calculate_and_award_points

urlpatterns = [

    path('update/calculate_award', Calculate_and_award_points, name="calculate-award_points"),


]



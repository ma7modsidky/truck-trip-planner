from django.urls import path

from api.views import plan_trip


urlpatterns = [
    path("plan-trip/", plan_trip, name="plan-trip"),
]
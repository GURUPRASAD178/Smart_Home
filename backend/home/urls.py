from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.status),
    path("readings/", views.readings),
    path("events/", views.events),
    path("devices/<str:name>/", views.device),
    path("config/", views.config),
    path("alarm/", views.alarm),
    path("sim/", views.sim),
]

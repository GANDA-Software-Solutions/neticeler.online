from django.urls import path

from . import views

app_name = "results"

urlpatterns = [
    path("", views.home, name="home"),
    path("yukle/<int:pk>/", views.download_result, name="download"),
    path("bax/<int:pk>/", views.view_result, name="view"),
]

from django.contrib import admin
from django.urls import path

from .views import SimpleModelDetailView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "simplemodel/<int:pk>/",
        SimpleModelDetailView.as_view(),
        name="simplemodel-detail",
    ),
]

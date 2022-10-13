from django.contrib import admin
from django.urls import path

from auditlog_tests.views import SimpleModelDetailview

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "simplemodel/<int:pk>/",
        SimpleModelDetailview.as_view(),
        name="simplemodel-detail",
    ),
]

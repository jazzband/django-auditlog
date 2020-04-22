import django
from django.conf.urls import include, url
from django.contrib import admin


if django.VERSION < (1, 9):
    admin_urls = include(admin.site.urls)
else:
    admin_urls = admin.site.urls

urlpatterns = [
    url(r'^admin/', admin_urls),
]

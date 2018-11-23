from django.conf.urls import url
from django.contrib import admin


admin_urls = admin.site.urls

urlpatterns = [
    url(r'^admin/', admin_urls),
]

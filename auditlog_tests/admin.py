from django.contrib import admin

from auditlog.registry import auditlog

for model in auditlog.get_models():
    admin.site.register(model)

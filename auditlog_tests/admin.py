from django.contrib import admin

from auditlog.registry import get_default_auditlogs

for auditlog in get_default_auditlogs():
    for model in auditlog.get_models():
        admin.site.register(model)

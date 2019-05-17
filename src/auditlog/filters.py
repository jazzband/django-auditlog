from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType
from django.db.models import Value
from django.db.models.functions import Concat

from auditlog.registry import auditlog


class ResourceTypeFilter(SimpleListFilter):
    title = 'Resource Type'
    parameter_name = 'resource_type'

    def lookups(self, request, model_admin):
        tracked_model_names = [
            '{}.{}'.format(m._meta.app_label, m._meta.model_name)
            for m in auditlog.list()
        ]
        model_name_concat = Concat('app_label', Value('.'), 'model')
        content_types = ContentType.objects.annotate(
            model_name=model_name_concat,
        ).filter(
            model_name__in=tracked_model_names,
        )
        return content_types.order_by('model_name').values_list('id', 'model_name')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(content_type_id=self.value())

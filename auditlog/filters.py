from django.apps import apps
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.filters import DateFieldListFilter
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import connection
from django.db.models import Value
from django.db.models.functions import Concat, Cast

from auditlog.registry import auditlog


class ShortActorFilter(SimpleListFilter):
    title = "Actor"
    parameter_name = "actor"

    def lookups(self, request, model_admin):
        return [("null", "System"), ("not_null", "Users")]

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset
        if value == "null":
            return queryset.filter(actor__isnull=True)
        return queryset.filter(actor__isnull=False)


class ResourceTypeFilter(SimpleListFilter):
    title = "Resource Type"
    parameter_name = "resource_type"

    def lookups(self, request, model_admin):
        tracked_model_names = [
            "{}.{}".format(m._meta.app_label, m._meta.model_name)
            for m in auditlog.list()
        ]
        model_name_concat = Concat("app_label", Value("."), "model")
        content_types = ContentType.objects.annotate(
            model_name=model_name_concat,
        ).filter(
            model_name__in=tracked_model_names,
        )
        return content_types.order_by("model_name").values_list("id", "model_name")

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(content_type_id=self.value())


class FieldFilter(SimpleListFilter):
    title = "Field"
    parameter_name = "field"
    parent = ResourceTypeFilter

    def __init__(self, request, *args, **kwargs):
        self.target_model = self._get_target_model(request)
        super().__init__(request, *args, **kwargs)

    def _get_target_model(self, request):
        # the parameters consumed by previous filters aren't passed to subsequent filters,
        # so we have to look into the request parameters explicitly
        content_type_id = request.GET.get(self.parent.parameter_name)
        if not content_type_id:
            return None

        return ContentType.objects.get(id=content_type_id).model_class()

    def lookups(self, request, model_admin):
        if connection.vendor != "postgresql":
            # filtering inside JSON is PostgreSQL-specific for now
            return []
        if not self.target_model:
            return []
        return sorted(
            (field.name, field.name) for field in self.target_model._meta.fields
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.annotate(changes_json=Cast("changes", JSONField())).filter(
            **{"changes_json__{}__isnull".format(self.value()): False}
        )


def get_timestamp_filter():
    """Returns rangefilter filter class if able or a simple list filter as a fallback."""
    if apps.is_installed("rangefilter"):
        try:
            from rangefilter.filter import DateTimeRangeFilter

            return DateTimeRangeFilter
        except ImportError:
            pass

    return DateFieldListFilter

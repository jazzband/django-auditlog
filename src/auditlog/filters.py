from django.contrib.admin import SimpleListFilter


class ResourceTypeFilter(SimpleListFilter):
    title = 'Resource Type'
    parameter_name = 'resource_type'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        types = qs.values_list('content_type_id', 'content_type__model')
        return list(types.order_by('content_type__model').distinct())

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(content_type_id=self.value())

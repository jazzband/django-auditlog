from django.contrib.admin import SimpleListFilter
from django.forms.utils import pretty_name
from elasticsearch_dsl import Q


class SimpleInputFilter(SimpleListFilter):
    template = 'admin/input_filter.html'

    def __init__(self, request, params, model, model_admin, parameter_name=None):
        if parameter_name:
            self.parameter_name = parameter_name
            self.title = pretty_name(self.parameter_name)
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def queryset(self, request, queryset):
        term = self.value()
        if term is None:
            return
        return queryset.query('query_string', query=f'*{term}*', fields=[self.parameter_name])

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class ActorInputFilter(SimpleInputFilter):
    parameter_name = 'actor'
    title = 'Actor'

    def queryset(self, request, queryset):
        term = self.value()
        if term is None:
            return
        return queryset.query(
            Q('match', actor_id=term) |
            Q('query_string', query=f'*{term}*', fields=['actor_first_name', 'actor_last_name', 'actor_email'])
        )

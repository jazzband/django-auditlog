from collections import OrderedDict

from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import AdminSplitDateTime
from django.forms import forms, SplitDateTimeField
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


class DateTimeFilter(SimpleInputFilter):
    def __init__(self, request, params, model, model_admin, field_path):
        self.lookup_kwarg_gte = 'from'
        self.lookup_kwarg_lte = 'to'
        super().__init__(request, params, model, model_admin, field_path)
        self.form = self.get_form(request)

    def queryset(self, request, queryset):
        if self.form.is_valid():
            validated_data = dict(self.form.cleaned_data.items())
            if validated_data:
                return queryset.filter(
                    'range', **{self.parameter_name: self._make_query_filter(validated_data)}
                )
        return queryset

    def _get_form_fields(self):
        return OrderedDict(
            (
                (self.lookup_kwarg_lte, SplitDateTimeField(
                    label='',
                    widget=AdminSplitDateTime(attrs={'style': 'width: 50%', 'placeholder': 'From'}),
                    required=False
                )),
                (self.lookup_kwarg_gte, SplitDateTimeField(
                    label='',
                    widget=AdminSplitDateTime(attrs={'style': 'width: 50%', 'placeholder': 'To'}),
                    required=False
                )),
            )
        )

    def get_form(self, request):
        fields = self._get_form_fields()

        form_class = type(
            str('DateRangeForm'),
            (forms.BaseForm,),
            {'base_fields': fields}
        )
        return form_class(request.GET)

    def _make_query_filter(self, validated_data):
        query_params = {}
        date_value_gte = validated_data.get(self.lookup_kwarg_gte, None)
        date_value_lte = validated_data.get(self.lookup_kwarg_lte, None)

        if date_value_gte:
            query_params['gte'] = date_value_gte
        if date_value_lte:
            query_params['lte'] = date_value_lte
        return query_params

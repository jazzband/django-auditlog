from collections import OrderedDict
from functools import reduce

from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import AdminSplitDateTime, AdminTextInputWidget
from django.contrib.contenttypes.models import ContentType
from django.forms import forms, SplitDateTimeField, CharField, ChoiceField
from django.forms.utils import pretty_name
from elasticsearch_dsl import Q

from auditlog.documents import LogEntry


class SimpleInputFilter(SimpleListFilter):
    template = 'admin/input_filter.html'

    def __init__(self, request, params, model, model_admin, parameter_name=None):
        if parameter_name:
            self.parameter_name = parameter_name
            self.title = pretty_name(self.parameter_name)
        super().__init__(request, params, model, model_admin)
        self.form = self.get_form(request)

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

    def _get_form_fields(self):
        return OrderedDict(
            (
                (self.parameter_name, CharField(
                    label='',
                    required=False
                )),
            )
        )

    def get_form(self, request):
        fields = self._get_form_fields()

        form_class = type(
            str('CustomFilterForm'),
            (forms.BaseForm,),
            {'base_fields': fields}
        )
        return form_class(request.GET)


class ActorInputFilter(SimpleInputFilter):
    parameter_name = 'actor'
    title = 'Actor'

    def queryset(self, request, queryset):
        if self.form.is_valid():
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

    def queryset(self, request, queryset):
        if self.form.is_valid():
            validated_data = dict(self.form.cleaned_data.items())
            if validated_data:
                query_params = self._make_query_filter(validated_data)
                if query_params:
                    return queryset.filter(
                        'range', **{self.parameter_name: query_params}
                    )
        return None

    def _get_form_fields(self):
        return OrderedDict(
            (
                (self.lookup_kwarg_gte, SplitDateTimeField(
                    label='',
                    widget=AdminSplitDateTime(attrs={'style': 'width: 50%', 'placeholder': 'From'}),
                    required=False
                )),
                (self.lookup_kwarg_lte, SplitDateTimeField(
                    label='',
                    widget=AdminSplitDateTime(attrs={'style': 'width: 50%', 'placeholder': 'To'}),
                    required=False
                )),
            )
        )

    def _make_query_filter(self, validated_data):
        query_params = {}
        date_value_gte = validated_data.get(self.lookup_kwarg_gte, None)
        date_value_lte = validated_data.get(self.lookup_kwarg_lte, None)

        if date_value_gte:
            query_params['gte'] = date_value_gte
        if date_value_lte:
            query_params['lte'] = date_value_lte
        return query_params


class BaseChoiceFilter(SimpleInputFilter):
    field_choices = None

    def _get_form_fields(self):
        return OrderedDict(
            (
                (self.parameter_name, ChoiceField(
                    label='',
                    required=False,
                    choices=self.field_choices
                )),
            )
        )


class ActionChoiceFilter(BaseChoiceFilter):
    parameter_name = 'action'
    title = 'Action'
    field_choices = LogEntry.Action.choices


class ContentTypeChoiceFilter(BaseChoiceFilter):
    parameter_name = 'content_type_id'
    title = 'Content type'
    field_choices = ContentType.objects.values_list('id', 'model')


class ChangesFilter(SimpleInputFilter):
    parameter_name = 'changes'
    title = 'Changes'

    def __init__(self, request, params, model, model_admin):
        self.lookup_kwarg_field = 'field'
        self.lookup_kwarg_new = 'new'
        self.lookup_kwarg_old = 'old'
        super().__init__(request, params, model, model_admin, self.parameter_name)

    def _get_form_fields(self):
        return OrderedDict(
            (
                (self.lookup_kwarg_field, CharField(
                    label='',
                    required=False,
                    widget=AdminTextInputWidget(attrs={'placeholder': self.lookup_kwarg_field})
                )),
                (self.lookup_kwarg_new, CharField(
                    label='',
                    required=False,
                    widget=AdminTextInputWidget(attrs={'placeholder': self.lookup_kwarg_new})
                )),
                (self.lookup_kwarg_old, CharField(
                    label='',
                    required=False,
                    widget=AdminTextInputWidget(attrs={'placeholder': self.lookup_kwarg_old})
                )),
            )
        )

    def queryset(self, request, queryset):
        if self.form.is_valid():
            validated_data = dict(self.form.cleaned_data.items())
            if validated_data:
                query_params = self._make_query_filter(validated_data)
                if query_params:
                    return queryset.filter(
                        'nested',
                        path='changes',
                        query=reduce(lambda a, b: a & b, query_params)
                    )
        return None

    def _make_query_filter(self, validated_data):
        changes_field = validated_data.get(self.lookup_kwarg_field, None)
        changes_new = validated_data.get(self.lookup_kwarg_new, None)
        changes_old = validated_data.get(self.lookup_kwarg_old, None)
        query_params = []
        if changes_field:
            query_params.append(Q('term', **{f'{self.parameter_name}__{self.lookup_kwarg_field}': changes_field}))
        if changes_new:
            query_params.append(Q('term', **{f'{self.parameter_name}__{self.lookup_kwarg_new}': changes_new}))
        if changes_old:
            query_params.append(Q('term', **{f'{self.parameter_name}__{self.lookup_kwarg_old}': changes_old}))
        return query_params

from math import ceil
from urllib.parse import urlencode

from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ALL_VAR, PAGE_VAR
from django.core.paginator import InvalidPage, Paginator
from django.forms.utils import pretty_name
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import format_html

from filters import SimpleInputFilter


def get_headers(fields):
    for field in fields:
        yield {
            'text': pretty_name(field),
            'class_attrib': format_html(' class="column-{}"', field),
            'sortable': False,
        }


def items_for_result(result, fields, opts):
    first = True
    for field in fields:

        value = getattr(result, field)

        if first:
            first = False
            url = reverse(
                'admin:%s_%s_change' % (opts.app_label, opts.model_name),
                args=(result.id,),
                # current_app=self.model_admin.admin_site.name
            )
            link_or_text = format_html(
                '<a href="{}">{}</a>',
                url,
                value
            )
            yield format_html('<th>{}</th>', link_or_text)
        else:
            yield format_html('<td>{}</td>', value)


def results(result_list, fields, opts):
    for result in result_list:
        yield items_for_result(result, fields, opts)


class CustomPaginator(Paginator):
    @cached_property
    def num_pages(self):
        """Return the total number of pages."""
        if self.count == 0 and not self.allow_empty_first_page:
            return 0
        hits = max(1, self.count - self.orphans)
        # Elasticsearch has max offset 10000
        if hits > 10000:
            hits = 10000
        return ceil(hits / self.per_page)


class CustomChangeList:
    def __init__(self, model_admin, request, list_filter):
        self.model_admin = model_admin
        self.request = request
        self.params = dict(request.GET.items())
        self.root_queryset = model_admin.get_queryset(request)
        self.list_filter = list_filter

    def get_filters_params(self, params=None):
        """
        Return all params except IGNORED_PARAMS.
        """
        params = params or self.params
        lookup_params = params.copy()  # a dictionary of the query string
        return lookup_params

    def get_filters(self):
        lookup_params = self.get_filters_params()
        has_active_filters = False

        filter_specs = []
        for list_filter in self.list_filter:
            lookup_params_count = len(lookup_params)
            if callable(list_filter):
                # This is simply a custom list filter class.
                spec = list_filter(self.request, lookup_params, self.model_admin.model, self.model_admin)
            else:
                if isinstance(list_filter, (tuple, list)):
                    # This is a custom FieldListFilter class for a given field.
                    field, field_list_filter_class = list_filter
                else:
                    # This is simply a field name, so use the default
                    # SimpleInputFilter class that has been registered for the
                    # type of the given field.
                    field_list_filter_class = SimpleInputFilter
                    field = list_filter

                spec = field_list_filter_class(
                    self.request,
                    lookup_params,
                    self.model_admin.model,
                    self.model_admin,
                    field
                )
            if spec and spec.has_output():
                filter_specs.append(spec)
                if lookup_params_count > len(lookup_params):
                    has_active_filters = True
        return (
            filter_specs, bool(filter_specs),
            has_active_filters,
        )

    def get_queryset(self):
        # First, we collect all the declared list filters.
        (
            self.filter_specs,
            self.has_filters,
            self.has_active_filters,
        ) = self.get_filters()
        # Then, we let every list filter modify the queryset to its liking.
        qs = self.root_queryset
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(self.request, qs)
            if new_qs is not None:
                qs = new_qs

        # # Set ordering.
        # ordering = self.get_ordering(request, qs)
        # qs = qs.order_by(*ordering)
        #
        # # Apply search results
        # qs, search_use_distinct = self.model_admin.get_search_results(request, qs, self.query)

        # # Set query string for clearing all filters.
        # self.clear_all_filters_qs = self.get_query_string(
        #     new_params=remaining_lookup_params,
        #     remove=self.get_filters_params(),
        # )
        return qs

    def get_results(self):
        queryset = self.get_queryset()
        paginator = self.model_admin.get_paginator(self.request, queryset, self.model_admin.list_per_page)
        # Get the number of objects, with admin filters applied.
        result_count = paginator.count

        # Get the total number of objects, with no admin filters applied.
        if self.model_admin.show_full_result_count:
            full_result_count = self.root_queryset.count()
        else:
            full_result_count = None

        can_show_all = result_count <= self.model_admin.list_max_show_all
        multi_page = result_count > self.model_admin.list_per_page

        try:
            page_num = int(self.request.GET.get(PAGE_VAR, 0))
        except ValueError:
            page_num = 0

        show_all = ALL_VAR in self.request.GET
        # Get the list of objects to display on this page.
        if (show_all and can_show_all) or not multi_page:
            result_list = queryset._clone()
        else:
            try:
                result_list = paginator.page(page_num + 1).object_list
            except InvalidPage:
                raise IncorrectLookupParameters

        self.result_count = result_count
        self.show_full_result_count = self.model_admin.show_full_result_count
        self.show_admin_actions = False
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator
        self.page_num = page_num
        self.show_all = show_all

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))

import elasticsearch
from django.contrib import admin
from django.db import models
from django.http import Http404
from django.shortcuts import render
from django.urls import path

from auditlog.filters import ActorInputFilter, DateTimeFilter
from .documents import LogEntry
from .mixins import LogEntryAdminMixin
from .utils.admin import get_headers, results, CustomChangeList, CustomPaginator


class DummyLogModel(models.Model):
    class Meta:
        verbose_name_plural = 'Log Entries'
        app_label = 'auditlog'


class DummyModelAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_fields = ['timestamp', 'action', 'content_type_model', 'object_repr', 'actor']
    filters = [ActorInputFilter, 'object_repr', ('timestamp', DateTimeFilter)]
    detail_fields = {
        'Details': ('created', 'user', 'resource'),
        'Changes': ('action', 'changes')
    }

    paginator = CustomPaginator
    readonly_fields = []

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path('', self.list_view, name='%s_%s_changelist' % info),
            path('<path:object_id>/', self.detail_view, name='%s_%s_change' % info),
        ]

    def get_queryset(self, request):
        s = LogEntry.search()
        s = s.sort('-timestamp')
        return s

    def list_view(self, request):
        cl = CustomChangeList(self, request, list_filter=self.filters)
        cl.get_results()

        context = {
            'title': 'Log entries',
            'opts': self.model._meta,
            'cl': cl,
            'result_headers': get_headers(self.list_fields),
            'num_sorted_fields': 0,
            'results': list(results(cl.result_list, self.list_fields, self.model._meta)),
        }

        return render(request, 'admin/logs_list.html', context=context)

    def detail_view(self, request, object_id):
        try:
            obj = LogEntry.get(object_id)
        except elasticsearch.exceptions.NotFoundError:
            raise Http404()
        context = {
            'opts': self.model._meta,
            'title': str(obj),
            'fieldsets': self._get_obj_fields(obj)
        }
        return render(request, 'admin/logs_detail.html', context=context)

    def _get_obj_fields(self, obj):
        fields = {}
        for key, values in self.detail_fields.items():
            fields[key] = []
            for value in values:
                if hasattr(self, value):
                    val = getattr(self, value)
                    if callable(val):
                        fields[key].append((value, val(obj)))
                else:
                    fields[key].append((value, getattr(obj, value)))
        return fields


admin.site.register(DummyLogModel, DummyModelAdmin)

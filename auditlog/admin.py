from django.contrib import admin
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path

from filters import ActorInputFilter
from .documents import LogEntry
from .utils.admin import get_headers, results, CustomChangeList, CustomPaginator


class DummyLogModel(models.Model):
    class Meta:
        verbose_name_plural = 'Log Entries'
        app_label = 'auditlog'


class DummyModelAdmin(admin.ModelAdmin):
    list_fields = ['timestamp', 'action', 'object_repr', 'actor']
    filters = [ActorInputFilter, 'object_repr']

    paginator = CustomPaginator

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path('', self.list_view, name='%s_%s_changelist' % info),
            path('<path:object_id>/change/', self.detail_view, name='%s_%s_change' % info),
        ]

    def get_queryset(self, request):
        s = LogEntry.search()
        s = s.sort('-timestamp')
        return s

    def list_view(self, request):
        cl = CustomChangeList(self, request, list_filter=self.filters)
        cl.get_results()

        context = {
            'title': 'Log entries', 'opts': self.model._meta,
            'cl': cl,
            'result_headers': get_headers(self.list_fields),
            'num_sorted_fields': 0,
            'results': list(results(cl.result_list, self.list_fields, self.model._meta)),
        }

        return render(request, 'admin/logs_list.html', context=context)

    def detail_view(self, request, object_id):
        return HttpResponse("Detail view works!")


admin.site.register(DummyLogModel, DummyModelAdmin)

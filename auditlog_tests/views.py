from django.views.generic import DetailView

from auditlog.mixins import LogAccessMixin
from auditlog_tests.models import SimpleModel


class SimpleModelDetailview(LogAccessMixin, DetailView):
    model = SimpleModel
    template_name = "simplemodel_detail.html"

from django.views.generic import DetailView

from auditlog.mixins import LogAccessMixin

from .models import SimpleModel


class SimpleModelDetailView(LogAccessMixin, DetailView):
    model = SimpleModel
    template_name = "simplemodel_detail.html"

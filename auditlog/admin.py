from functools import cached_property

from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from auditlog.filters import CIDFilter, ResourceTypeFilter
from auditlog.mixins import LogEntryAdminMixin
from auditlog.models import LogEntry


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_select_related = ["content_type", "actor"]
    list_display = [
        "created",
        "resource_url",
        "action",
        "msg_short",
        "user_url",
        "cid_url",
    ]
    search_fields = [
        "timestamp",
        "object_repr",
        "changes",
        "actor__first_name",
        "actor__last_name",
        f"actor__{get_user_model().USERNAME_FIELD}",
    ]
    list_filter = ["action", ResourceTypeFilter, CIDFilter]
    readonly_fields = ["created", "resource_url", "action", "user_url", "msg"]
    fieldsets = [
        (None, {"fields": ["created", "user_url", "resource_url", "cid"]}),
        (_("Changes"), {"fields": ["action", "msg"]}),
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @cached_property
    def _own_url_names(self):
        return [pattern.name for pattern in self.urls if pattern.name]

    def has_delete_permission(self, request, obj=None):
        if (
            request.resolver_match
            and request.resolver_match.url_name not in self._own_url_names
        ):
            # only allow cascade delete to satisfy delete_related flag
            return super().has_delete_permission(request, obj)
        return False

    def get_queryset(self, request):
        self.request = request
        queryset = super().get_queryset(request=request)

        # Check for the `ss` parameter for structured search
        structured_search = request.GET.get("ss")
        if structured_search:
            # Parse structured search term as 'ModelName:id'
            try:
                model_name, object_id = structured_search.split(":")
                object_id = int(object_id)
            except (ValueError, TypeError):
                # If the format is incorrect, return an empty queryset and show a message
                if not getattr(request, "_message_shown", False):
                    self.message_user(
                        request,
                        "Structured search format must be 'ModelName:id'.",
                        level="warning",
                    )
                    request._message_shown = True
                return queryset.none()

            # Attempt to retrieve the specified model
            try:
                model = apps.get_model(app_label="api", model_name=model_name)
                if not model:
                    raise LookupError
            except LookupError:
                if not getattr(request, "_message_shown", False):
                    self.message_user(
                        request,
                        f"Model '{model_name}' does not exist.",
                        level="warning",
                    )
                    request._message_shown = True
                return queryset.none()

            # Attempt to retrieve the object and filter log entries
            try:
                model.objects.only("id").get(pk=object_id)  # Lookup.
                content_type = ContentType.objects.get_for_model(model)
                queryset = queryset.filter(
                    content_type=content_type, object_id=object_id
                )
            except ObjectDoesNotExist:
                if not getattr(request, "_message_shown", False):
                    self.message_user(
                        request,
                        f"{model_name} instance with ID {object_id} does not exist.",
                        level="warning",
                    )
                    request._message_shown = True
                return queryset.none()

        return queryset  # Return filtered or default queryset based on the presence of `ss`

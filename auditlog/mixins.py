import json

from django import urls as urlresolvers
from django.conf import settings
from django.urls.exceptions import NoReverseMatch
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from auditlog.models import LogEntry

MAX = 75


class LogEntryAdminMixin:
    def created(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    created.short_description = "Created"

    def user_url(self, obj):
        if obj.actor:
            app_label, model = settings.AUTH_USER_MODEL.split(".")
            viewname = f"admin:{app_label}_{model.lower()}_change"
            try:
                link = urlresolvers.reverse(viewname, args=[obj.actor.pk])
            except NoReverseMatch:
                return "%s" % (obj.actor)
            return format_html('<a href="{}">{}</a>', link, obj.actor)

        return "system"

    user_url.short_description = "User"

    def resource_url(self, obj):
        app_label, model = obj.content_type.app_label, obj.content_type.model
        viewname = f"admin:{app_label}_{model}_change"
        try:
            args = [obj.object_pk] if obj.object_id is None else [obj.object_id]
            link = urlresolvers.reverse(viewname, args=args)
        except NoReverseMatch:
            return obj.object_repr
        else:
            return format_html(
                '<a href="{}">{} - {}</a>', link, obj.content_type, obj.object_repr
            )

    resource_url.short_description = "Resource"

    def msg_short(self, obj):
        if obj.action == LogEntry.Action.DELETE:
            return ""  # delete
        changes = json.loads(obj.changes)
        s = "" if len(changes) == 1 else "s"
        fields = ", ".join(changes.keys())
        if len(fields) > MAX:
            i = fields.rfind(" ", 0, MAX)
            fields = fields[:i] + " .."
        return "%d change%s: %s" % (len(changes), s, fields)

    msg_short.short_description = "Changes"

    def msg(self, obj):
        if obj.action == LogEntry.Action.DELETE:
            return ""  # delete
        changes = json.loads(obj.changes)
        msg = "<table><tr><th>#</th><th>Field</th><th>From</th><th>To</th></tr>"
        for i, field in enumerate(sorted(changes), 1):
            value = [i, field] + (
                ["***", "***"] if field == "password" else changes[field]
            )
            msg += format_html(
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>", *value
            )

        msg += "</table>"
        return mark_safe(msg)

    msg.short_description = "Changes"

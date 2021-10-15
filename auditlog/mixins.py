import json

from django import urls as urlresolvers
from django.conf import settings
from django.db.models import DateTimeField
from django.template.defaultfilters import pluralize
from django.urls.exceptions import NoReverseMatch
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime

from auditlog.models import LogEntry

MAX = 75


class LogEntryAdminMixin(object):
    def created(self, obj):
        return localtime(obj.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    created.short_description = "Created"

    def user_url(self, obj):
        if obj.actor:
            app_label, model = settings.AUTH_USER_MODEL.split(".")
            viewname = "admin:%s_%s_change" % (app_label, model.lower())
            try:
                link = urlresolvers.reverse(viewname, args=[obj.actor.pk])
            except NoReverseMatch:
                return "%s" % (obj.actor)
            return format_html('<a href="{}">{}</a>', link, obj.actor)

        return "system"

    user_url.short_description = "User"

    def resource_url(self, obj):
        app_label, model = obj.content_type.app_label, obj.content_type.model
        viewname = "admin:%s_%s_change" % (app_label, model)
        try:
            args = [obj.object_pk] if obj.object_id is None else [obj.object_id]
            link = urlresolvers.reverse(viewname, args=args)
        except NoReverseMatch:
            return obj.object_repr
        else:
            return format_html('<a href="{}">{}</a>', link, obj.object_repr)

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

        atom_changes = {}
        m2m_changes = {}

        for field, change in changes.items():
            if isinstance(change, dict):
                assert (
                    change["type"] == "m2m"
                ), "Only m2m operations are expected to produce dict changes now"
                m2m_changes[field] = change
            else:
                atom_changes[field] = change

        msg = []
        spotted_datetime_field = False

        if atom_changes:
            datetime_fields = self._get_datetime_fields(obj)
            msg.append("<table>")
            msg.append(self._format_header("#", "Field", "From", "To"))
            for i, (field, change) in enumerate(sorted(atom_changes.items()), 1):
                value = [i, field] + (["***", "***"] if field == "password" else change)
                if field in datetime_fields:
                    spotted_datetime_field = True
                msg.append(self._format_line(*value))
            msg.append("</table>")

        if m2m_changes:
            msg.append("<table>")
            msg.append(self._format_header("#", "Relationship", "Action", "Objects"))
            for i, (field, change) in enumerate(sorted(m2m_changes.items()), 1):
                change_html = format_html_join(
                    mark_safe("</br>"),
                    "{}",
                    [(value,) for value in change["objects"]],
                )

                msg.append(
                    format_html(
                        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td>",
                        i,
                        field,
                        change["operation"],
                        change_html,
                    )
                )

            msg.append("</table>")

        if spotted_datetime_field:
            warning_message = self._get_timezone_warning()
            if warning_message:
                msg.append(warning_message)

        return mark_safe("".join(msg))

    msg.short_description = "Changes"

    def _get_datetime_fields(self, obj):
        # only works for existing models and existing fields
        try:
            return {
                field.name
                for field in obj.content_type.model_class()._meta.fields
                if isinstance(field, DateTimeField)
            }
        except Exception:
            return set()

    def _format_header(self, *labels):
        return format_html(
            "".join(["<tr>", "<th>{}</th>" * len(labels), "</tr>"]), *labels
        )

    def _format_line(self, *values):
        return format_html(
            "".join(["<tr>", "<td>{}</td>" * len(values), "</tr>"]), *values
        )

    def _get_timezone_warning(self):
        offset_seconds = timezone.localtime().utcoffset().total_seconds()
        if not offset_seconds:
            return None

        ahead_behind = "ahead of" if offset_seconds < 0 else "behind"
        offset_seconds = abs(offset_seconds)
        hours, minutes = divmod(int(offset_seconds / 60), 60)
        hours = "{} hour{}".format(hours, pluralize(hours))
        minutes = " {} minute{}".format(minutes, pluralize(minutes)) if minutes else ""
        warning_message = (
            "Note: The timestamps are in UTC, which is {}{} {} server time".format(
                hours, minutes, ahead_behind
            )
        )
        return '<span class="timezonewarning">{}</span>'.format(warning_message)

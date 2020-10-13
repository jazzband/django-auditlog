from django import urls as urlresolvers
from django.conf import settings
from django.urls.exceptions import NoReverseMatch
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from auditlog.models import LogEntry


class LogEntryAdminMixin(object):

    def created(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')

    def user(self, obj):
        if obj.actor_id:
            app_label, model = settings.AUTH_USER_MODEL.split('.')
            viewname = 'admin:%s_%s_change' % (app_label, model.lower())
            try:
                link = urlresolvers.reverse(viewname, args=[obj.actor_id])
            except NoReverseMatch:
                return u'%s' % (obj.actor)
            return format_html(u'<a href="{}">{}</a>', link, obj.actor_email)

        return 'system'

    def resource(self, obj):
        app_label, model = obj.content_type_app_label, obj.content_type_model
        viewname = 'admin:%s_%s_change' % (app_label, model)
        try:
            args = [obj.object_pk] if obj.object_id is None else [obj.object_id]
            link = urlresolvers.reverse(viewname, args=args)
        except NoReverseMatch:
            return obj.object_repr
        else:
            return format_html(u'<a href="{}">{}</a>', link, obj.object_repr)

    def changes(self, obj):
        if obj.action == LogEntry.Action.DELETE or not obj.changes:
            return ''  # delete
        changes = obj.changes
        msg = '<table class="grp-table"><thead><tr><th>#</th><th>Field</th><th>From</th><th>To</th></tr></thead>'
        for i, change in enumerate(changes):
            class_ = [f"grp-row grp-row-{'event' if i % 2 else 'odd'}"]
            value = class_ + [i, change.field] + (['***', '***'] if change.field == 'password'
                                                  else [change.old, change.new])
            msg += format_html('<tr class="{}"><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>', *value)

        msg += '</table>'
        return mark_safe(msg)

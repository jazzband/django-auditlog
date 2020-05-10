import json

from django.conf import settings
try:
    from django.core import urlresolvers
except ImportError:
    from django import urls as urlresolvers
try:
    from django.urls.exceptions import NoReverseMatch
except ImportError:
    from django.core.urlresolvers import NoReverseMatch
from django.utils.html import format_html
from django.utils.safestring import mark_safe

MAX = 75


class LogEntryAdminMixin(object):

    def created(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    created.short_description = 'Created'

    def user_url(self, obj):
        if obj.actor:
            app_label, model = settings.AUTH_USER_MODEL.split('.')
            viewname = 'admin:%s_%s_change' % (app_label, model.lower())
            try:
                link = urlresolvers.reverse(viewname, args=[obj.actor.id])
            except NoReverseMatch:
                return u'%s' % (obj.actor)
            return format_html(u'<a href="{}">{}</a>', link, obj.actor)

        return 'system'
    user_url.short_description = 'User'

    def resource_url(self, obj):
        app_label, model = obj.content_type.app_label, obj.content_type.model
        viewname = 'admin:%s_%s_change' % (app_label, model)
        try:
            args = [obj.object_pk] if obj.object_id is None else [obj.object_id]
            link = urlresolvers.reverse(viewname, args=args)
        except NoReverseMatch:
            return obj.object_repr
        else:
            return format_html(u'<a href="{}">{}</a>', link, obj.object_repr)
    resource_url.short_description = 'Resource'

    def msg_short(self, obj):
        changes = json.loads(obj.changes)
        s = '' if len(changes) == 1 else 's'
        fields = ', '.join(changes.keys())
        if len(fields) > MAX:
            i = fields.rfind(' ', 0, MAX)
            fields = fields[:i] + ' ..'
        return '%d change%s: %s' % (len(changes), s, fields)

    msg_short.short_description = 'Changes'

    def msg(self, obj):
        changes = json.loads(obj.changes)

        field_changes = list()
        m2m_changes = list()

        for change in changes:
            if isinstance(changes[change][1], list):
                m2m_changes.append(change)
            else:
                field_changes.append(change)

        msg = ''

        # Render field changes
        if len(field_changes) > 0 and obj.action != 2:
            msg = '<table><tr><th>#</th><th>Field</th><th>From</th><th>To</th></tr>'
            for i, field in enumerate(sorted(field_changes), 1):
                value = [i, field] + (['***', '***'] if field == 'password' else changes[field])
                msg += format_html('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>', *value)
            msg += '</table>'

        if len(m2m_changes) > 0:
            msg += '<table><tr><th>#</th><th>Relationship</th><th>Action</th><th>Changed</th></tr>'
            for i, field in enumerate(sorted(m2m_changes), 1):
                change_html = ''
                for changed_data in changes[field][1]:
                    change_html += format_html('{}</br>', changed_data)

                msg += format_html('<tr><td>{}</td><td>{}</td><td>{}</td>', i, field, changes[field][0])
                msg += '<td>{}</td></tr>'.format(change_html)

            msg += '</table>'

        return mark_safe(msg)
    msg.short_description = 'Changes'

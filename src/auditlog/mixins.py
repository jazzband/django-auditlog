import json
import cgi

from django.conf import settings
from django.core import urlresolvers
from django.utils.html import format_html
try:
    from django.urls.exceptions import NoReverseMatch
except ImportError:
    from django.core.urlresolvers import NoReverseMatch

MAX = 75


class LogEntryAdminMixin(object):

    def created(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    created.short_description = 'Created'

    def user_url(self, obj):
        if obj.actor:
            app_label, model = settings.AUTH_USER_MODEL.split('.')
            viewname = 'admin:%s_%s_change' % (app_label, model.lower())
            link = urlresolvers.reverse(viewname, args=[obj.actor.id])
            return u'<a href="%s">%s</a>' % (link, obj.actor)

        return 'system'
    user_url.allow_tags = True
    user_url.short_description = 'User'

    def resource_url(self, obj):
        app_label, model = obj.content_type.app_label, obj.content_type.model
        viewname = 'admin:%s_%s_change' % (app_label, model)
        try:
            link = urlresolvers.reverse(viewname, args=[obj.object_id])
        except NoReverseMatch:
            return obj.object_repr
        else:
            return u'<a href="%s">%s</a>' % (link, obj.object_repr)
    resource_url.allow_tags = True
    resource_url.short_description = 'Resource'

    def remote_addr_url_w(self, obj):
        if obj.remote_addr is None:
            return None
        link = "https://ipinfo.io/" + str(obj.remote_addr)
        return u'%s [ <a target="_blank" href="%s">Lookup</a> ]' % (obj.remote_addr, link )
    remote_addr_url_w.allow_tags = True
    remote_addr_url_w.short_description = 'IP'

    def msg_short(self, obj):
        if obj.action == 2:
            return ''  # delete
        changes = json.loads(obj.changes)

	# single-field changes, display data
        if len(changes.keys())==1:
            html='<span style="font-size:0.8em; font-weight:900;">%s</span><br><span style="color:darkblue">%s</span> &rarr;  <span style="color:darkgreen">%s</span>'
            s=''
            for key in changes.keys():
                val = changes[key]
                s += format_html(html % (key ,  cgi.escape(val[0]),  cgi.escape(val[1]) ) )
            return s

	# multi-field changes, list fields
        fields = ', '.join(sorted(changes.keys()))
        if len(fields) > MAX:
            i = fields.rfind(' ', 0, MAX)
            fields = fields[:i] + ' ..'
        return '<span style="font-size:0.8em; font-weight:900;">%s</span>' % fields
    msg_short.short_description = 'Changes'
    msg_short.allow_tags = True

    def msg(self, obj):
        changes = json.loads(obj.changes)
        msg = '<table width="100%"><tr><th>#</th><th width="15%">Field</th><th width="40%">From</th><th width="40%">To</th></tr>'
        for i, field in enumerate(sorted(changes), 1):
            r=0
            value = [i, field] + (['***', '***'] if field == 'password' else changes[field])
            rc="row2" if r%2 else "row1"
            args = (rc,) + tuple(value)
            msg += '<tr class="%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' %  args
            r += 1
        msg += '</table>'
        return msg
    msg.allow_tags = True
    msg.short_description = 'Changes'

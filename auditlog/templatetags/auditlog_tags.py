from django import template

from auditlog.render import render_logentry_changes_html as render_changes

register = template.Library()


@register.filter
def render_logentry_changes_html(log_entry):
    """
    Format LogEntry changes as HTML.

    Usage in template:
    {{ log_entry_object|render_logentry_changes_html|safe }}
    """
    return render_changes(log_entry)

from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import pretty_name
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


def render_logentry_changes_html(log_entry):
    changes = log_entry.changes_dict
    if not changes:
        return ""

    atom_changes = {}
    m2m_changes = {}

    # Separate regular fields from M2M changes
    for field, change in changes.items():
        if isinstance(change, dict) and change.get("type") == "m2m":
            m2m_changes[field] = change
        else:
            atom_changes[field] = change

    html_parts = []

    # Render regular field changes
    if atom_changes:
        html_parts.append(_render_field_changes(log_entry, atom_changes))

    # Render M2M relationship changes
    if m2m_changes:
        html_parts.append(_render_m2m_changes(log_entry, m2m_changes))

    return mark_safe("".join(html_parts))


def get_field_verbose_name(log_entry, field_name):
    from auditlog.registry import auditlog

    model = log_entry.content_type.model_class()
    if model is None:
        return field_name

    # Try to get verbose name from auditlog mapping
    try:
        if auditlog.contains(model._meta.model):
            model_fields = auditlog.get_model_fields(model._meta.model)
            mapping_field_name = model_fields["mapping_fields"].get(field_name)
            if mapping_field_name:
                return mapping_field_name
    except KeyError:
        # Model definition in auditlog was probably removed
        pass

    # Fall back to Django field verbose_name
    try:
        field = model._meta.get_field(field_name)
        return pretty_name(getattr(field, "verbose_name", field_name))
    except FieldDoesNotExist:
        return pretty_name(field_name)


def _render_field_changes(log_entry, atom_changes):
    rows = []
    rows.append(_format_header("#", _("Field"), _("From"), _("To")))

    for i, (field, change) in enumerate(sorted(atom_changes.items()), 1):
        field_name = get_field_verbose_name(log_entry, field)
        values = ["***", "***"] if field == "password" else change
        rows.append(_format_row(i, field_name, *values))

    return f"<table>{''.join(rows)}</table>"


def _render_m2m_changes(log_entry, m2m_changes):
    rows = []
    rows.append(_format_header("#", _("Relationship"), _("Action"), _("Objects")))

    for i, (field, change) in enumerate(sorted(m2m_changes.items()), 1):
        field_name = get_field_verbose_name(log_entry, field)
        objects_html = format_html_join(
            mark_safe("<br>"),
            "{}",
            [(obj,) for obj in change["objects"]],
        )
        rows.append(_format_row(i, field_name, change["operation"], objects_html))

    return f"<table>{''.join(rows)}</table>"


def _format_header(*labels):
    return format_html("".join(["<tr>", "<th>{}</th>" * len(labels), "</tr>"]), *labels)


def _format_row(*values):
    return format_html("".join(["<tr>", "<td>{}</td>" * len(values), "</tr>"]), *values)

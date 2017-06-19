from django.db.models.signals import m2m_changed
import json
from functools import partial
from auditlog.models import LogEntry


def m2m_change_repr(model, pk_set):
    return [unicode(i) for i in model.objects.filter(pk__in=pk_set)]


def m2m_changed_handler(sender, instance, model, action, pk_set, field_name, **kw):
    removed_str = added_str = ""
    if action == "post_add":
        added_str = m2m_change_repr(model, pk_set)
    if action == "post_remove":
        removed_str = m2m_change_repr(model, pk_set)
    if added_str or removed_str:
        changes = {field_name: [removed_str, added_str]}
        new = LogEntry.objects.log_create(
            instance,
            action=LogEntry.Action.UPDATE,
            changes=json.dumps(changes),
            add_data={'op':action,'m2m':True,'field':field_name,'object':model._meta.model_name,'app':model._meta.app_label,'ids':list(pk_set)},
        )

def auditlog_register_m2m(m2m):
    """
    Register m2m model field to track by auditlog
    """
    handler = partial(m2m_changed_handler, field_name=m2m.field.name)
    m2m_changed.connect(handler, sender=m2m.through, weak=False)


from auditlog.registry import AuditlogModelRegistry

create_only_auditlog = AuditlogModelRegistry(
    create=True,
    update=False,
    delete=False,
    access=False,
    m2m=False,
)
update_only_auditlog = AuditlogModelRegistry(
    create=False,
    update=True,
    delete=False,
    access=False,
    m2m=False,
)

from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder

AUDITLOG_BUGGY_REPR_DATATYPES = (Decimal,)


class AuditLogChangesJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, list) and obj:
            return [
                str(o) if isinstance(o, AUDITLOG_BUGGY_REPR_DATATYPES) else o
                for o in obj
            ]

        return super().default(obj)

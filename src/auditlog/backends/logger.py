import logging

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_text

from auditlog import settings
from auditlog.models import LogEntry
from auditlog.backends.base import AuditBackend
from auditlog.middleware import get_thread_data


class LoggerBackend(AuditBackend):
    """Python logger based backend for creation of audit log entries."""
    message = '{action} on {content_type_name} {object_pk} by actor {actor_name}'
    logger = 'audit.log'

    def get_level(self):
        """Returns the level """
        return settings.AUDITLOG_LEVEL

    def get_logger(self):
        """Returns an the python logger for logging audit messages"""
        return logging.getLogger(settings.AUDITLOG_LOGGER)

    def get_extra(self, action, instance, changes):
        """Returns a dictionary of extra data to be passed to the logger"""

        object_pk = LogEntry.objects._get_pk_value(instance)

        if changes is not None:
            get_additional_data = getattr(instance, 'get_additional_data', None)
            content_type_name = ContentType.objects.get_for_model(instance).name
            object_repr = smart_text(instance)
            additional_data = get_additional_data() if callable(get_additional_data) else None

        else:
            additional_data = None
            content_type_name = None
            object_repr = None

        thread_data = get_thread_data()

        actor_pk = thread_data.get('actor_pk')
        actor_name = thread_data.get('actor_name')
        remote_addr = thread_data.get('remote_addr')

        return {
            'action': str(LogEntry.Action.text(action)),
            'actor_pk': actor_pk,
            'actor_name': actor_name,
            'remote_addr': remote_addr,
            'object_pk': object_pk,
            'content_type_name': content_type_name,
            'object_repr': object_repr,
            'additional_data': additional_data,
            'changes': changes,
        }

    def create_log(self, action, instance, changes, **kwargs):
        """Generates a log entry for the given action and instance"""
        logger = self.get_logger()
        extra = self.get_extra(action, instance, changes)
        message = self.message.format(**extra)
        logger.log(level=self.get_level(), msg=message, extra=extra)

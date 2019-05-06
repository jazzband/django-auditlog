import uuid

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from auditlog.models import AuditLogHistoryMixin
from auditlog.registry import auditlog

from multiselectfield import MultiSelectField


@auditlog.register()
class SimpleModel(models.Model, AuditLogHistoryMixin):
    """
    A simple model with no special things going on.
    """

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)


class AltPrimaryKeyModel(models.Model, AuditLogHistoryMixin):
    """
    A model with a non-standard primary key.
    """
    pk_indexable = False
    key = models.CharField(max_length=100, primary_key=True)

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)


class UUIDPrimaryKeyModel(models.Model, AuditLogHistoryMixin):
    """
    A model with a UUID primary key.
    """
    pk_indexable = False
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)


class ProxyModel(SimpleModel, AuditLogHistoryMixin):
    """
    A model that is a proxy for another model.
    """

    class Meta:
        proxy = True


class RelatedModel(models.Model, AuditLogHistoryMixin):
    """
    A model with a foreign key.
    """

    related = models.ForeignKey(to='self', on_delete=models.CASCADE)


class ManyRelatedModel(models.Model, AuditLogHistoryMixin):
    """
    A model with a many to many relation.
    """

    related = models.ManyToManyField('self')


@auditlog.register(include_fields=['label'])
class SimpleIncludeModel(models.Model, AuditLogHistoryMixin):
    """
    A simple model used for register's include_fields kwarg
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)


class SimpleExcludeModel(models.Model, AuditLogHistoryMixin):
    """
    A simple model used for register's exclude_fields kwarg
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)


class SimpleMappingModel(models.Model, AuditLogHistoryMixin):
    """
    A simple model used for register's mapping_fields kwarg
    """

    sku = models.CharField(max_length=100)
    vtxt = models.CharField(verbose_name='Version', max_length=100)
    not_mapped = models.CharField(max_length=100)


class AdditionalDataIncludedModel(models.Model, AuditLogHistoryMixin):
    """
    A model where get_additional_data is defined which allows for logging extra
    information about the model in JSON
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    related = models.ForeignKey(to=SimpleModel, on_delete=models.CASCADE)

    def get_additional_data(self):
        """
        Returns JSON that captures a snapshot of additional details of the
        model instance. This method, if defined, is accessed by auditlog
        manager and added to each logentry instance on creation.
        """
        object_details = {
            'related_model_id': self.related.id,
            'related_model_text': self.related.text
        }
        return object_details


class DateTimeFieldModel(models.Model, AuditLogHistoryMixin):
    """
    A model with a DateTimeField, used to test DateTimeField
    changes are detected properly.
    """
    label = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    date = models.DateField()
    time = models.TimeField()
    naive_dt = models.DateTimeField(null=True, blank=True)


class ChoicesFieldModel(models.Model, AuditLogHistoryMixin):
    """
    A model with a CharField restricted to a set of choices.
    This model is used to test the changes_display_dict method.
    """
    RED = 'r'
    YELLOW = 'y'
    GREEN = 'g'

    STATUS_CHOICES = (
        (RED, 'Red'),
        (YELLOW, 'Yellow'),
        (GREEN, 'Green'),
    )

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    multiselect = MultiSelectField(max_length=3, choices=STATUS_CHOICES, max_choices=3)
    multiplechoice = models.CharField(max_length=3, choices=STATUS_CHOICES)


class CharfieldTextfieldModel(models.Model, AuditLogHistoryMixin):
    """
    A model with a max length CharField and a Textfield.
    This model is used to test the changes_display_dict
    method's ability to truncate long text.
    """

    longchar = models.CharField(max_length=255)
    longtextfield = models.TextField()


class PostgresArrayFieldModel(models.Model, AuditLogHistoryMixin):
    """
    Test auditlog with Postgres's ArrayField
    """
    RED = 'r'
    YELLOW = 'y'
    GREEN = 'g'

    STATUS_CHOICES = (
        (RED, 'Red'),
        (YELLOW, 'Yellow'),
        (GREEN, 'Green'),
    )

    arrayfield = ArrayField(models.CharField(max_length=1, choices=STATUS_CHOICES), size=3)



class NoDeleteHistoryModel(models.Model, AuditLogHistoryMixin):
    integer = models.IntegerField(blank=True, null=True)


auditlog.register(AltPrimaryKeyModel)
auditlog.register(UUIDPrimaryKeyModel)
auditlog.register(ProxyModel)
auditlog.register(RelatedModel)
auditlog.register(ManyRelatedModel)
auditlog.register(ManyRelatedModel.related.through)
auditlog.register(SimpleExcludeModel, exclude_fields=['text'])
auditlog.register(SimpleMappingModel, mapping_fields={'sku': 'Product No.'})
auditlog.register(AdditionalDataIncludedModel)
auditlog.register(DateTimeFieldModel)
auditlog.register(ChoicesFieldModel)
auditlog.register(CharfieldTextfieldModel)
auditlog.register(PostgresArrayFieldModel)
auditlog.register(NoDeleteHistoryModel)

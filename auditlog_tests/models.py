import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from auditlog.models import AuditlogHistoryField
from auditlog.registry import AuditlogModelRegistry, auditlog

m2m_only_auditlog = AuditlogModelRegistry(create=False, update=False, delete=False)


@auditlog.register()
class SimpleModel(models.Model):
    """
    A simple model with no special things going on.
    """

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)

    history = AuditlogHistoryField(delete_related=True)

    def __str__(self):
        return self.text


class AltPrimaryKeyModel(models.Model):
    """
    A model with a non-standard primary key.
    """

    key = models.CharField(max_length=100, primary_key=True)

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)

    history = AuditlogHistoryField(delete_related=True, pk_indexable=False)


class UUIDPrimaryKeyModel(models.Model):
    """
    A model with a UUID primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)

    history = AuditlogHistoryField(delete_related=True, pk_indexable=False)


class ProxyModel(SimpleModel):
    """
    A model that is a proxy for another model.
    """

    class Meta:
        proxy = True


class RelatedModelParent(models.Model):
    """
    Use multi table inheritance to make a OneToOneRel field
    """


class RelatedModel(RelatedModelParent):
    """
    A model with a foreign key.
    """

    related = models.ForeignKey(
        "SimpleModel", related_name="related_models", on_delete=models.CASCADE
    )
    one_to_one = models.OneToOneField(
        to="SimpleModel", on_delete=models.CASCADE, related_name="reverse_one_to_one"
    )

    history = AuditlogHistoryField(delete_related=True)


class ManyRelatedModel(models.Model):
    """
    A model with many-to-many relations.
    """

    recursive = models.ManyToManyField("self")
    related = models.ManyToManyField("ManyRelatedOtherModel", related_name="related")

    history = AuditlogHistoryField(delete_related=True)

    def get_additional_data(self):
        related = self.related.first()
        return {"related_model_id": related.id if related else None}


class ManyRelatedOtherModel(models.Model):
    """
    A model related to ManyRelatedModel as many-to-many.
    """

    history = AuditlogHistoryField(delete_related=True)


@auditlog.register(include_fields=["label"])
class SimpleIncludeModel(models.Model):
    """
    A simple model used for register's include_fields kwarg
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)

    history = AuditlogHistoryField(delete_related=True)


class SimpleExcludeModel(models.Model):
    """
    A simple model used for register's exclude_fields kwarg
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)

    history = AuditlogHistoryField(delete_related=True)


class SimpleMappingModel(models.Model):
    """
    A simple model used for register's mapping_fields kwarg
    """

    sku = models.CharField(max_length=100)
    vtxt = models.CharField(verbose_name="Version", max_length=100)
    not_mapped = models.CharField(max_length=100)

    history = AuditlogHistoryField(delete_related=True)


@auditlog.register(mask_fields=["address"])
class SimpleMaskedModel(models.Model):
    """
    A simple model used for register's mask_fields kwarg
    """

    address = models.CharField(max_length=100)
    text = models.TextField()

    history = AuditlogHistoryField(delete_related=True)


class AdditionalDataIncludedModel(models.Model):
    """
    A model where get_additional_data is defined which allows for logging extra
    information about the model in JSON
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    related = models.ForeignKey(to=SimpleModel, on_delete=models.CASCADE)

    history = AuditlogHistoryField(delete_related=True)

    def get_additional_data(self):
        """
        Returns JSON that captures a snapshot of additional details of the
        model instance. This method, if defined, is accessed by auditlog
        manager and added to each logentry instance on creation.
        """
        object_details = {
            "related_model_id": self.related.id,
            "related_model_text": self.related.text,
        }
        return object_details


class DateTimeFieldModel(models.Model):
    """
    A model with a DateTimeField, used to test DateTimeField
    changes are detected properly.
    """

    label = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    date = models.DateField()
    time = models.TimeField()
    naive_dt = models.DateTimeField(null=True, blank=True)

    history = AuditlogHistoryField(delete_related=True)


class ChoicesFieldModel(models.Model):
    """
    A model with a CharField restricted to a set of choices.
    This model is used to test the changes_display_dict method.
    """

    RED = "r"
    YELLOW = "y"
    GREEN = "g"

    STATUS_CHOICES = (
        (RED, "Red"),
        (YELLOW, "Yellow"),
        (GREEN, "Green"),
    )

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    multiplechoice = models.CharField(max_length=255, choices=STATUS_CHOICES)

    history = AuditlogHistoryField(delete_related=True)


class CharfieldTextfieldModel(models.Model):
    """
    A model with a max length CharField and a Textfield.
    This model is used to test the changes_display_dict
    method's ability to truncate long text.
    """

    longchar = models.CharField(max_length=255)
    longtextfield = models.TextField()

    history = AuditlogHistoryField(delete_related=True)


class PostgresArrayFieldModel(models.Model):
    """
    Test auditlog with Postgres's ArrayField
    """

    RED = "r"
    YELLOW = "y"
    GREEN = "g"

    STATUS_CHOICES = (
        (RED, "Red"),
        (YELLOW, "Yellow"),
        (GREEN, "Green"),
    )

    arrayfield = ArrayField(
        models.CharField(max_length=1, choices=STATUS_CHOICES), size=3
    )

    history = AuditlogHistoryField(delete_related=True)


class NoDeleteHistoryModel(models.Model):
    integer = models.IntegerField(blank=True, null=True)

    history = AuditlogHistoryField(delete_related=False)


class JSONModel(models.Model):
    json = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    history = AuditlogHistoryField(delete_related=False)


class SerializeThisModel(models.Model):
    label = models.CharField(max_length=24, unique=True)
    timestamp = models.DateTimeField()
    nullable = models.IntegerField(null=True)
    nested = models.JSONField()
    mask_me = models.CharField(max_length=255, null=True)
    code = models.UUIDField(null=True)
    date = models.DateField(null=True)

    history = AuditlogHistoryField(delete_related=False)

    def natural_key(self):
        return self.label


class SerializeOnlySomeOfThisModel(models.Model):
    this = models.CharField(max_length=24)
    not_this = models.CharField(max_length=24)

    history = AuditlogHistoryField(delete_related=False)


class SerializePrimaryKeyRelatedModel(models.Model):
    serialize_this = models.ForeignKey(to=SerializeThisModel, on_delete=models.CASCADE)
    subheading = models.CharField(max_length=255)
    value = models.IntegerField()

    history = AuditlogHistoryField(delete_related=False)


class SerializeNaturalKeyRelatedModel(models.Model):
    serialize_this = models.ForeignKey(to=SerializeThisModel, on_delete=models.CASCADE)
    subheading = models.CharField(max_length=255)
    value = models.IntegerField()

    history = AuditlogHistoryField(delete_related=False)


class SimpleNonManagedModel(models.Model):
    """
    A simple model with no special things going on.
    """

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)

    history = AuditlogHistoryField(delete_related=True)

    def __str__(self):
        return self.text

    class Meta:
        managed = False


class AutoManyRelatedModel(models.Model):
    related = models.ManyToManyField(SimpleModel)


auditlog.register(AltPrimaryKeyModel)
auditlog.register(UUIDPrimaryKeyModel)
auditlog.register(ProxyModel)
auditlog.register(RelatedModel)
auditlog.register(ManyRelatedModel)
auditlog.register(ManyRelatedModel.recursive.through)
m2m_only_auditlog.register(ManyRelatedModel, m2m_fields={"related"})
auditlog.register(SimpleExcludeModel, exclude_fields=["text"])
auditlog.register(SimpleMappingModel, mapping_fields={"sku": "Product No."})
auditlog.register(AdditionalDataIncludedModel)
auditlog.register(DateTimeFieldModel)
auditlog.register(ChoicesFieldModel)
auditlog.register(CharfieldTextfieldModel)
auditlog.register(PostgresArrayFieldModel)
auditlog.register(NoDeleteHistoryModel)
auditlog.register(JSONModel)
auditlog.register(
    SerializeThisModel,
    serialize_data=True,
    mask_fields=["mask_me"],
)
auditlog.register(
    SerializeOnlySomeOfThisModel,
    serialize_data=True,
    serialize_auditlog_fields_only=True,
    exclude_fields=["not_this"],
)
auditlog.register(SerializePrimaryKeyRelatedModel, serialize_data=True)
auditlog.register(
    SerializeNaturalKeyRelatedModel,
    serialize_data=True,
    serialize_kwargs={"use_natural_foreign_keys": True},
)

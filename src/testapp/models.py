from django.db import models
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog


class SimpleModel(models.Model):
    """
    A simple model with no special things going on.
    """

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)

    history = AuditlogHistoryField()


class AltPrimaryKeyModel(models.Model):
    """
    A model with a non-standard primary key.
    """

    key = models.CharField(max_length=100, primary_key=True)

    text = models.TextField(blank=True)
    boolean = models.BooleanField(default=False)
    integer = models.IntegerField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now=True)

    history = AuditlogHistoryField(pk_indexable=False)


class ProxyModel(SimpleModel):
    """
    A model that is a proxy for another model.
    """

    class Meta:
        proxy = True


class RelatedModel(models.Model):
    """
    A model with a foreign key.
    """

    related = models.ForeignKey('self')

    history = AuditlogHistoryField()


class ManyRelatedModel(models.Model):
    """
    A model with a many to many relation.
    """

    related = models.ManyToManyField('self')

    history = AuditlogHistoryField()


class SimpleIncludeModel(models.Model):
    """
    A simple model used for register's include_fields kwarg
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)

    history = AuditlogHistoryField()


class SimpleExcludeModel(models.Model):
    """
    A simple model used for register's exclude_fields kwarg
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)

    history = AuditlogHistoryField()


class AdditionDataIncludedModel(models.Model):
    """
    A model where get_additional_data is defined which allows for logging extra
    information about the model in JSON
    """

    label = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    related = models.ForeignKey(SimpleModel)

    history = AuditlogHistoryField()

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

auditlog.register(SimpleModel)
auditlog.register(AltPrimaryKeyModel)
auditlog.register(ProxyModel)
auditlog.register(SimpleIncludeModel, include_fields=['label', ])
auditlog.register(SimpleExcludeModel, exclude_fields=['label', ])
auditlog.register(AdditionDataIncludedModel)

import json
from datetime import timezone
from typing import Optional

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import NOT_PROVIDED, DateTimeField, ForeignKey, JSONField, Model
from django.utils import timezone as django_timezone
from django.utils.encoding import smart_str


def track_field(field):
    """
    Returns whether the given field should be tracked by Auditlog.

    Untracked fields are many-to-many relations and relations to the Auditlog LogEntry model.

    :param field: The field to check.
    :type field: Field
    :return: Whether the given field should be tracked.
    :rtype: bool
    """
    from auditlog.models import LogEntry

    # Do not track many to many relations
    if field.many_to_many:
        return False

    # Do not track relations to LogEntry
    if (
        getattr(field, "remote_field", None) is not None
        and field.remote_field.model == LogEntry
    ):
        return False

    return True


def get_fields_in_model(instance):
    """
    Returns the list of fields in the given model instance. Checks whether to use the official
    _meta API or use the raw data. This method excludes many to many fields.

    :param instance: The model instance to get the fields for
    :type instance: Model
    :return: The list of fields for the given model (instance)
    :rtype: list
    """
    assert isinstance(instance, Model)

    return [f for f in instance._meta.get_fields() if track_field(f)]


def get_field_value(obj, field):
    """
    Gets the value of a given model instance field.

    :param obj: The model instance.
    :type obj: Model
    :param field: The field you want to find the value of.
    :type field: Any
    :return: The value of the field as a string.
    :rtype: str
    """
    try:
        if isinstance(field, DateTimeField):
            # DateTimeFields are timezone-aware, so we need to convert the field
            # to its naive form before we can accurately compare them for changes.
            value = field.to_python(getattr(obj, field.name, None))
            if (
                value is not None
                and settings.USE_TZ
                and not django_timezone.is_naive(value)
            ):
                value = django_timezone.make_naive(value, timezone=timezone.utc)
        elif isinstance(field, JSONField):
            value = field.to_python(getattr(obj, field.name, None))
            value = json.dumps(value, sort_keys=True, cls=field.encoder)
        elif (field.one_to_one or field.many_to_one) and hasattr(field, "rel_class"):
            value = smart_str(
                getattr(obj, field.get_attname(), None), strings_only=True
            )
        else:
            value = smart_str(getattr(obj, field.name, None))
            if type(value).__name__ == "__proxy__":
                value = str(value)
    except ObjectDoesNotExist:
        value = (
            field.default
            if getattr(field, "default", NOT_PROVIDED) is not NOT_PROVIDED
            else None
        )

    return value


def mask_str(value: str) -> str:
    """
    Masks the first half of the input string to remove sensitive data.

    :param value: The value to mask.
    :type value: str
    :return: The masked version of the string.
    :rtype: str
    """
    mask_limit = int(len(value) / 2)
    return "*" * mask_limit + value[mask_limit:]


def model_instance_diff(
    old: Optional[Model], new: Optional[Model], fields_to_check=None
):
    """
    Calculates the differences between two model instances. One of the instances may be ``None``
    (i.e., a newly created model or deleted model). This will cause all fields with a value to have
    changed (from ``None``).

    :param old: The old state of the model instance.
    :type old: Model
    :param new: The new state of the model instance.
    :type new: Model
    :param fields_to_check: An iterable of the field names to restrict the diff to, while ignoring the rest of
        the model's fields. This is used to pass the `update_fields` kwarg from the model's `save` method.
    :type fields_to_check: Iterable
    :return: A dictionary with the names of the changed fields as keys and a two tuple of the old and new
            field values as value.
    :rtype: dict
    """
    from auditlog.registry import auditlog

    if not (old is None or isinstance(old, Model)):
        raise TypeError("The supplied old instance is not a valid model instance.")
    if not (new is None or isinstance(new, Model)):
        raise TypeError("The supplied new instance is not a valid model instance.")

    diff = {}

    if old is not None and new is not None:
        fields = set(old._meta.fields + new._meta.fields)
        model_fields = auditlog.get_model_fields(new._meta.model)
    elif old is not None:
        fields = set(get_fields_in_model(old))
        model_fields = auditlog.get_model_fields(old._meta.model)
    elif new is not None:
        fields = set(get_fields_in_model(new))
        model_fields = auditlog.get_model_fields(new._meta.model)
    else:
        fields = set()
        model_fields = None

    if fields_to_check:
        fields = {
            field
            for field in fields
            if (
                (isinstance(field, ForeignKey) and field.attname in fields_to_check)
                or (field.name in fields_to_check)
            )
        }

    # Check if fields must be filtered
    if (
        model_fields
        and (model_fields["include_fields"] or model_fields["exclude_fields"])
        and fields
    ):
        filtered_fields = []
        if model_fields["include_fields"]:
            filtered_fields = [
                field
                for field in fields
                if field.name in model_fields["include_fields"]
            ]
        else:
            filtered_fields = fields
        if model_fields["exclude_fields"]:
            filtered_fields = [
                field
                for field in filtered_fields
                if field.name not in model_fields["exclude_fields"]
            ]
        fields = filtered_fields

    for field in fields:
        old_value = get_field_value(old, field)
        new_value = get_field_value(new, field)

        if old_value != new_value:
            if model_fields and field.name in model_fields["mask_fields"]:
                diff[field.name] = (
                    mask_str(smart_str(old_value)),
                    mask_str(smart_str(new_value)),
                )
            else:
                diff[field.name] = (smart_str(old_value), smart_str(new_value))

    if len(diff) == 0:
        diff = None

    return diff

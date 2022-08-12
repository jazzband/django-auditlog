from functools import cached_property
from typing import Any, Dict, List, Union

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import NOT_PROVIDED, DateTimeField, JSONField, Model
from django.utils import timezone
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
            if value is not None and settings.USE_TZ and not timezone.is_naive(value):
                value = timezone.make_naive(value, timezone=timezone.utc)
        elif isinstance(field, JSONField):
            value = field.to_python(getattr(obj, field.name, None))
        else:
            value = smart_str(getattr(obj, field.name, None))
    except ObjectDoesNotExist:
        value = field.default if field.default is not NOT_PROVIDED else None

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


class MaskedDictionary:
    """Mask a dictionary's string values that relate to key paths."""

    def __init__(self, data: Dict[str, Any], mask_fields: List[str]):
        """
        Constructor.

        :param data: The dictionary with values to be masked
        :param mask_fields: A list of field names which require their values masked
        """
        self.data = data
        self._mask_fields = mask_fields

    def mask_it(self) -> Dict[str, Any]:
        """
        Generates a new masked dictionary.

        :rtype: dict
        """
        return self._mask_dict(dictionary=self.data.copy(), parent_key_path=[])

    @cached_property
    def _unpacked_mask_fields(self) -> List[List[str]]:
        unpacked = []
        for field in self._mask_fields:
            unpacked += [[x for x in field.split("__") if x]]
        return unpacked

    def _get_masked_keys_at_depth(self, parent_key_path: List[str]) -> List[str]:
        masked_keys = []
        depth = len(parent_key_path)
        if depth == 0:
            return [x[0] for x in self._unpacked_mask_fields]

        applicable_paths = [x for x in self._unpacked_mask_fields if len(x) > depth]
        for key_path in applicable_paths:
            if key_path[:depth] == parent_key_path:
                masked_keys.append(key_path[depth])

        return masked_keys

    def _mask_iterable(
        self,
        iterable: Union[tuple, set, list],
        parent_key_path: List[str],
        this_key: str,
    ) -> Union[tuple, set, list]:
        masked_keys = self._get_masked_keys_at_depth(parent_key_path)
        is_masked_field = bool(this_key in masked_keys)
        sanitized_iterable = []

        for item in iterable:
            if isinstance(item, str):
                sanitized_iterable.append(mask_str(item) if is_masked_field else item)
            elif isinstance(item, dict):
                sanitized_iterable.append(
                    self._mask_dict(item, [*parent_key_path, this_key])
                )
            elif hasattr(item, "__iter__"):
                sanitized_iterable.append(
                    self._mask_iterable(item, parent_key_path, this_key)
                )
            else:
                sanitized_iterable.append(item)

        return sanitized_iterable

    def _mask_dict(self, dictionary: Dict[str, Any], parent_key_path: List[str]):
        masked_keys = self._get_masked_keys_at_depth(parent_key_path)
        sanitized_dict = {}

        for key, value in dictionary.items():
            is_masked_field = bool(key in masked_keys)
            if isinstance(value, str):
                sanitized_dict[key] = mask_str(value) if is_masked_field else value
            elif isinstance(value, dict):
                sanitized_dict[key] = self._mask_dict(value, [*parent_key_path, key])
            elif hasattr(value, "__iter__"):
                sanitized_dict[key] = self._mask_iterable(value, parent_key_path, key)
            else:
                sanitized_dict[key] = value

        return sanitized_dict


def model_instance_diff(old, new, fields_to_check=None):
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
        fields = {field for field in fields if field.name in fields_to_check}

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

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.encoding import force_str

from rest_framework import exceptions, serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import clone_request
from collections import OrderedDict
from rest_framework.metadata import BaseMetadata
from rest_framework.utils.field_mapping import ClassLookupDict


class WalaxModelMetadata(BaseMetadata):
    """
    This is the default metadata implementation.
    It returns an ad-hoc set of information about the view.
    There are not any formalized standards for `OPTIONS` responses
    for us to base this on.
    """

    label_lookup = ClassLookupDict(
        {
            serializers.Field: "field",
            serializers.PrimaryKeyRelatedField: "related",
            serializers.RelatedField: "related",
            serializers.BooleanField: "boolean",
            serializers.NullBooleanField: "boolean",
            serializers.CharField: "string",
            serializers.UUIDField: "string",
            serializers.URLField: "url",
            serializers.EmailField: "email",
            serializers.RegexField: "regex",
            serializers.SlugField: "slug",
            serializers.IntegerField: "integer",
            serializers.FloatField: "float",
            serializers.DecimalField: "decimal",
            serializers.DateField: "date",
            serializers.DateTimeField: "datetime",
            serializers.TimeField: "time",
            serializers.ChoiceField: "choice",
            serializers.MultipleChoiceField: "multiple choice",
            serializers.FileField: "file upload",
            serializers.ImageField: "image upload",
            serializers.ListField: "list",
            serializers.DictField: "nested object",
            serializers.Serializer: "nested object",
        }
    )

    def determine_metadata(self, request, view):
        metadata = OrderedDict()
        metadata["name"] = view.get_view_name()
        metadata["description"] = view.get_view_description()
        metadata["renders"] = [
            renderer.media_type for renderer in view.renderer_classes
        ]
        metadata["parses"] = [
            parser.media_type for parser in view.parser_classes]
        metadata["model"] = view.queryset.model.__name__
        self.model = view.queryset.model
        metadata['extra_actions'] = self.determine_extra_actions(request, view)

        if hasattr(view, "get_serializer"):
            actions = self.determine_actions(request, view)
            if actions:
                metadata["actions"] = actions
        return metadata

    def determine_extra_actions(self, request, view):
        """
        Return list of extra callable actions
        """
        import inspect
        actions = []
        for fn, f in [(fn, f) for (fn, f) in inspect.getmembers(self.model) if inspect.isfunction(f) and getattr(f, 'walax_action', False)]:
            actions.append({
                'method': 'post',
                'type': 'instance',
                'name': fn
            })
        return actions

    def determine_actions(self, request, view):
        """
        For generic class based views we return information about
        the fields that are accepted for 'PUT' and 'POST' methods.
        """
        actions = {}
        for method in {"PUT", "POST"} & set(view.allowed_methods):
            view.request = clone_request(request, method)
            try:
                # Test global permissions
                if hasattr(view, "check_permissions"):
                    view.check_permissions(view.request)
                # Test object permissions
                if method == "PUT" and hasattr(view, "get_object"):
                    view.get_object()
            except (exceptions.APIException, PermissionDenied, Http404):
                pass
            else:
                # If user has appropriate permissions for the view, include
                # appropriate metadata about the fields that should be supplied.
                serializer = view.get_serializer()
                actions[method] = self.get_serializer_info(serializer)
            finally:
                view.request = request
        return actions

    def get_serializer_info(self, serializer):
        """
        Given an instance of a serializer, return a dictionary of metadata
        about its fields.
        """
        if hasattr(serializer, "child"):
            # If this is a `ListSerializer` then we want to examine the
            # underlying child serializer instance instead.
            serializer = serializer.child
        return OrderedDict(
            [
                (field_name, self.get_field_info(field, field_name))
                for field_name, field in serializer.fields.items()
                if not isinstance(field, serializers.HiddenField)
            ]
        )

    def get_field_info(self, field, field_name):
        """
        Given an instance of a serializer field, return a dictionary
        of metadata about it.
        """
        field_info = OrderedDict()
        field_info["type"] = self.label_lookup[field]
        field_info["required"] = getattr(field, "required", False)
        if field_info["type"].startswith("related"):
            field_info["model"] = field.queryset.model.__name__
            field_info["related_name"] = getattr(field, "related_name", None)

        attrs = [
            "read_only",
            "label",
            "help_text",
            "min_length",
            "max_length",
            "min_value",
            "max_value",
            "related_name",
        ]

        if getattr(self.model._meta.get_field(field_name), "primary_key", False):
            field_info["primary_key"] = "true"

        for attr in attrs:
            value = getattr(field, attr, None)
            if value is not None and value != "":
                field_info[attr] = force_str(value, strings_only=True)

        if getattr(field, "child", None):
            field_info["child"] = self.get_field_info(field.child)
        elif getattr(field, "fields", None):
            field_info["children"] = self.get_serializer_info(field)

        if (
            not field_info.get("read_only")
            and not isinstance(
                field, (serializers.RelatedField, serializers.ManyRelatedField)
            )
            and hasattr(field, "choices")
        ):
            field_info["choices"] = [
                {
                    "value": choice_value,
                    "display_name": force_str(choice_name, strings_only=True),
                }
                for choice_value, choice_name in field.choices.items()
            ]

        return field_info

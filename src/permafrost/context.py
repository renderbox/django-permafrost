from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

DEFAULT_CONTEXT_MODEL = "sites.Site"
DEFAULT_CONTEXT_REQUEST_ATTR = "site"


def get_context_model_label():
    return getattr(settings, "PERMAFROST_CONTEXT_MODEL", DEFAULT_CONTEXT_MODEL)


def get_context_model():
    try:
        return apps.get_model(get_context_model_label(), require_ready=False)
    except (LookupError, ValueError) as exc:
        raise ImproperlyConfigured(
            "PERMAFROST_CONTEXT_MODEL must be an app_label.ModelName string."
        ) from exc


def get_context_content_type(context_object=None):
    context_model = get_context_model()
    if context_object is not None:
        context_model = context_object._meta.model
    return ContentType.objects.get_for_model(context_model)


def get_default_context_object():
    context_model = get_context_model()
    if context_model is Site:
        return Site.objects.get_current()

    manager = context_model._default_manager
    try:
        return manager.get_current()
    except AttributeError as exc:
        raise ImproperlyConfigured(
            "PERMAFROST_CONTEXT_MODEL must provide a get_current() manager method "
            "or the current context must be passed explicitly."
        ) from exc


def get_request_context_object(request):
    request_attr = getattr(
        settings, "PERMAFROST_CONTEXT_REQUEST_ATTR", DEFAULT_CONTEXT_REQUEST_ATTR
    )
    context_object = getattr(request, request_attr, None)
    if context_object is not None:
        return context_object

    if request_attr != "site":
        context_object = getattr(request, "site", None)
        if context_object is not None and get_context_model() is Site:
            return context_object

    return get_default_context_object()


def get_context_filter(context_object):
    return {
        "context_content_type": get_context_content_type(context_object),
        "context_object_id": context_object.pk,
    }

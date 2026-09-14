from django.conf import settings
from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.checks import Error, Warning, register


@register()
def check_permafrost_settings(app_configs, **kwargs):
    messages = []
    context_model = getattr(settings, "PERMAFROST_CONTEXT_MODEL", "sites.Site")
    try:
        apps.get_model(context_model)
    except (LookupError, ValueError):
        messages.append(
            Error(
                "PERMAFROST_CONTEXT_MODEL does not point to an installed model.",
                hint="Use an app_label.ModelName string such as 'sites.Site' or 'accounts.Organization'.",
                id="permafrost.E007",
            )
        )

    categories = getattr(settings, "PERMAFROST_CATEGORIES", None)

    if categories is None:
        messages.append(
            Error(
                "PERMAFROST_CATEGORIES is not configured.",
                hint="Define PERMAFROST_CATEGORIES in settings before using Permafrost role views.",
                id="permafrost.E001",
            )
        )
        return messages

    if not isinstance(categories, dict):
        messages.append(
            Error(
                "PERMAFROST_CATEGORIES must be a dictionary.",
                id="permafrost.E002",
            )
        )
        return messages

    if not hasattr(settings, "PERMAFROST_DEFAULT_ROLES"):
        messages.append(
            Warning(
                "PERMAFROST_DEFAULT_ROLES is not configured.",
                hint="Set PERMAFROST_DEFAULT_ROLES to a list of protected role names, or [] if none should be protected by name.",
                id="permafrost.W001",
            )
        )

    for category_key, category_data in categories.items():
        if not isinstance(category_data, dict):
            messages.append(
                Error(
                    f"PERMAFROST_CATEGORIES['{category_key}'] must be a dictionary.",
                    id="permafrost.E003",
                )
            )
            continue

        for permission_type in ("required", "optional"):
            permission_items = category_data.get(permission_type, [])
            if not isinstance(permission_items, (list, tuple)):
                messages.append(
                    Error(
                        f"PERMAFROST_CATEGORIES['{category_key}']['{permission_type}'] must be a list or tuple.",
                        id="permafrost.E004",
                    )
                )
                continue

            for permission_item in permission_items:
                permission_key = permission_item.get("permission")
                if not permission_key:
                    messages.append(
                        Error(
                            f"PERMAFROST_CATEGORIES['{category_key}'] contains a {permission_type} permission without a permission natural key.",
                            id="permafrost.E005",
                        )
                    )
                    continue

                try:
                    Permission.objects.get_by_natural_key(*permission_key)
                except (Permission.DoesNotExist, TypeError, ValueError):
                    messages.append(
                        Error(
                            f"Permission {permission_key!r} in PERMAFROST_CATEGORIES['{category_key}']['{permission_type}'] does not exist.",
                            hint="Run migrations and verify the permission natural key is (codename, app_label, model).",
                            id="permafrost.E006",
                        )
                    )

    return messages

from django.apps import AppConfig


class PermafrostConfig(AppConfig):
    name = "permafrost"

    def ready(self):
        from . import checks  # noqa: F401

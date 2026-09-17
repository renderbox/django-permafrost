import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Count


def validate_existing_role_integrity(apps, schema_editor):
    PermafrostRole = apps.get_model("permafrost", "PermafrostRole")
    db_alias = schema_editor.connection.alias
    roles = PermafrostRole.objects.using(db_alias)

    duplicate_slugs = list(
        roles.values("context_content_type_id", "context_object_id", "slug")
        .annotate(role_count=Count("id"))
        .filter(role_count__gt=1)
    )
    shared_groups = list(
        roles.exclude(group_id=None)
        .values("group_id")
        .annotate(role_count=Count("id"))
        .filter(role_count__gt=1)
    )

    if duplicate_slugs or shared_groups:
        raise RuntimeError(
            "Cannot enforce Permafrost role integrity. Resolve duplicate role "
            f"slugs {duplicate_slugs!r} and shared Groups {shared_groups!r}, "
            "then run migrations again."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("permafrost", "0021_alter_permafrostrole_site"),
    ]

    operations = [
        migrations.RunPython(
            validate_existing_role_integrity,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="permafrostrole",
            name="group",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="permafrost_role",
                to="auth.group",
                verbose_name="Group",
            ),
        ),
        migrations.AddConstraint(
            model_name="permafrostrole",
            constraint=models.UniqueConstraint(
                fields=("slug", "context_content_type", "context_object_id"),
                name="unique_role_slug_per_context",
            ),
        ),
    ]

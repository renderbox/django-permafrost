# Generated by Django 2.2.10 on 2020-02-18 22:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("auth", "0011_update_proxy_permissions"),
        ("permafrost", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PermafrostRole",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="Name")),
                ("slug", models.SlugField(verbose_name="Slug")),
                (
                    "category",
                    models.IntegerField(
                        choices=[(1, "User"), (30, "Staff"), (50, "Administrator")],
                        default=1,
                        verbose_name="Permafrost Role Category",
                    ),
                ),
                ("locked", models.BooleanField(default=False, verbose_name="Locked")),
                (
                    "group",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auth.Group",
                        verbose_name="Group",
                    ),
                ),
                (
                    "site",
                    models.ForeignKey(
                        default=1,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sites.Site",
                    ),
                ),
            ],
            options={
                "verbose_name": "Role",
                "verbose_name_plural": "Roles",
                "unique_together": {("name", "site")},
            },
        ),
        migrations.DeleteModel(
            name="Role",
        ),
    ]

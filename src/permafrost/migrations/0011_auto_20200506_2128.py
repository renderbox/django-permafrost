# Generated by Django 3.0.6 on 2020-05-06 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0011_update_proxy_permissions"),
        ("permafrost", "0010_auto_20200504_2344"),
    ]

    operations = [
        migrations.AlterField(
            model_name="permafrostrole",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="permafrost_role",
                to="auth.Group",
                verbose_name="Group",
            ),
        ),
    ]
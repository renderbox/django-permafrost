# Generated by Django 3.1.3 on 2021-04-06 18:20

from django.db import migrations, models
import django.db.models.deletion
import permafrost.models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("permafrost", "0018_auto_20201124_1534"),
    ]

    operations = [
        migrations.AlterField(
            model_name="permafrostrole",
            name="site",
            field=models.ForeignKey(
                default=permafrost.models.get_current_site,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="permafrost_role",
                to="sites.site",
            ),
        ),
    ]

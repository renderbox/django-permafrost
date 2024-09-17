# Generated by Django 3.0.3 on 2020-03-13 21:59

from django.db import migrations, models
import django.db.models.deletion
import permafrost.models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("permafrost", "0005_auto_20200311_1701"),
    ]

    operations = [
        migrations.AlterField(
            model_name="permafrostrole",
            name="site",
            field=models.ForeignKey(
                default=permafrost.models.get_current_site,
                on_delete=django.db.models.deletion.CASCADE,
                to="sites.Site",
            ),
        ),
    ]

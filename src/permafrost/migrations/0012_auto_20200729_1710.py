# Generated by Django 3.0.7 on 2020-07-29 17:10

import django.contrib.sites.managers
from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ("permafrost", "0011_auto_20200506_2128"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="permafrostrole",
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("on_site", django.contrib.sites.managers.CurrentSiteManager()),
            ],
        ),
    ]

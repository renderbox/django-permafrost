# Generated by Django 3.0.3 on 2020-03-19 00:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("permafrost", "0006_auto_20200313_2056"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="permafrostrole",
            name="group",
        ),
    ]

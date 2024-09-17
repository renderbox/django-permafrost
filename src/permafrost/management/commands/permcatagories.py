#--------------------------------------------
# Copyright 2013-2019, Grant Viklund
# @Author: Grant Viklund
# @Date:   2017-02-20 13:50:51
# @Last Modified by:   Grant Viklund
# @Last Modified time: 2019-12-21 15:12:35
#--------------------------------------------

# https://timonweb.com/posts/how-to-get-a-list-of-all-user-permissions-available-in-django-based-project/

# import os
# import subprocess
# import json
# import fileinput

import pprint

from django.core.management.base import BaseCommand
from django.conf import settings
# from django.contrib.auth import get_user_model, get_backends
from django.contrib.auth.models import Permission
from permafrost.models import PermafrostCategory

class Command(BaseCommand):

    help = "Print out the exitsing PermafrostCategories in Python Dictionary format for migrating to the new code based format."
    debug = settings.DEBUG

    def handle(self, *args, **options):

        try:
            self.process_permission_list()

        except KeyboardInterrupt:
            print("\nExiting...")
            return

    def process_permission_list(self):
        categories = PermafrostCategory.objects.all()

        print("PermafrostCategory formatted for your code\n")

        data = {}

        for category in categories:            # Permission's Natural Key = codename + content_type.natural_key()      "{1}.{0}".format(*perm.natural_key())
            data[category.slug] = {
                "label": category.name,
                "level": category.level,
                "optional": [],
                "required": []
            }

            for item in category.permissions:
                app_lable, codename = item['perm'].split(".")
                perm = Permission.objects.get(codename=codename, content_type__app_label=app_lable )
                data[category.slug]["optional"].append( perm )

            for item in category.includes:
                app_lable, codename = item.split(".")
                perm = Permission.objects.get(codename=codename, content_type__app_label=app_lable )
                data[category.slug]["required"].append( perm )

        key_order = list(data.keys())
        key_order.sort()

        print("from django.utils.translation import gettext_lazy as _\n")

        print("PERMAFROST_CATEGORIES = {")

        for key in key_order:
            print("    '{}': {{".format(key))
            print("        'label': _('{}'),".format(data[key]['label']))
            print("        'level': {},".format(data[key]['level']))

            if data[key]['optional']:
                print("        'optional': [")
                for item in data[key]['optional']:
                    print("            {{'label': _('{}'), 'permission': {} }},".format(item.name, item.natural_key()) )
                print("        ],")
            else:
                print("        'optional': [],")

            if data[key]['required']:
                print("        'required': [")
                for item in data[key]['required']:
                    print("            {{'label': _('{}'), 'permission': {} }},".format(item.name, item.natural_key()) )
                print("        ],")
            else:
                print("        'required': [],")

            print("    },")
        print("}\n")


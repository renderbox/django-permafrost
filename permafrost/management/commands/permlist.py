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

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model, get_backends
from django.contrib.auth.models import Permission

class Command(BaseCommand):

    help = "Get a list of all permissions in the system that can be set by the Client"
    debug = settings.DEBUG

    # def add_arguments(self, parser):

    #     parser.add_argument('source', type=str)

    #     parser.add_argument(
    #         # '-n', '--dry-run', action='store_true', dest='dry_run',
    #         # '-e', '--dry-run', action='store_true', dest='dry_run', # Same as Djando dump data
    #         help="Do everything except modify the filesystem.",
    #     )

    # def set_options(self, **options):
    #     """
    #     Set instance variables based on an options dict
    #     """
    #     self.dryrun = options['dry_run']
    #     self.source_data = os.path.abspath( options['source'] ) 

    def handle(self, *args, **options):
        # self.set_options(**options)

        try:
            self.process_permission_list()

        except KeyboardInterrupt:
            print("\nExiting...")
            return


    def process_permission_list(self):
        permissions = Permission.objects.all()

        ignore_apps = getattr(settings, "PERMAFROST_IGNORE_APPS", ['admin', 'auth', 'contenttypes', 'sessions', 'sites']) #, 'permafrost'])

        for perm in permissions:            # Permission's Natural Key = codename + content_type.natural_key()
            keys = list(perm.natural_key())
            if keys[1] not in ignore_apps:

                keys[2] = perm.name
                print( '{' + '"perm":"{1}.{0}", "label":"{2}"'.format( *keys ) + '},' )

        # print("\n")

        # for perm in permissions:
        #     print( perm )                   # Permission's __str__ = '%s | %s' % (self.content_type, self.name)


    # def process(self):
    #     permissions = set()
    #     ignore_list = []   

    #     tmp_superuser = get_user_model()( is_active=True, is_superuser=True )

    #     for backend in get_backends():
    #         if hasattr(backend, "get_all_permissions"):
    #             permissions.update(backend.get_all_permissions(tmp_superuser))

    #     # Make an unique list of permissions sorted by permission name.
    #     sorted_list_of_permissions = sorted(list(permissions))

    #     print(dir(sorted_list_of_permissions[0]))

    #     # Send a joined list of permissions to a command-line output.
    #     print('\n'.join(sorted_list_of_permissions))

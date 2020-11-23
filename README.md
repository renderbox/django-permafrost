![Permafrost Develop](https://github.com/renderbox/django-permafrost/workflows/Permafrost%20Develop/badge.svg)

![Permafrost CI](https://github.com/renderbox/django-permafrost/workflows/Permafrost%20CI/badge.svg)

[![Documentation Status](https://readthedocs.org/projects/django-permafrost/badge/?version=latest)](https://django-permafrost.readthedocs.io/en/latest/?badge=latest)

# Django Permafrost

Django Permafrost is an extension to Django's Permissions framework.  It's goal is to allow developers to expose some permissions to Client Users on the site so they can create and manage custom User Roles.

It adds:
- A View Mixin that supports user permissions based on different HTTP method types (GET, POST, PUT, etc) for extra granular control.
- A View Mixin that captures into Django's logging setup any failed permission checks.
- An App that supports Client User definable roles and permissions.  This uses the underlying Django Permission system and controls which permissions are exposed to the users.
  - Developers can have both require permissions for the permission classes or optional permission that can be set by the Client.

For example, you have a SAAS platform where you have Administrators Clients.  They manage the other users on their master account in the system (like Employees, etc) and want to be able to define different permissions for various users.  They might have one Employee they want to be able to manage email lists but not let them invite users but both are considered in the staff category.

## Installation

To install, just use pip

```shell
> pip install django-permafrost
```

To add it to your project, add it to the list of install apps in you `settings.py`...

```python

INSTALLED_APPS = [
    ...
    'permafrost',
    ...
]
```

... and migrate

```shell
> ./manage.py migrate
```

## Setup

The Goal of Django Permafrost is to allow Clients to create their own Permafrost Roles, under developer defined Categories with developer defined required and optional permissions.

An example of a developer defined categories looks like this:

```python
Sample Category Permission Format:

PERMAFROST_CATEGORIES = {
    'user': {
        'label': _("User"),
        'access_level': 1,
        'optional': [
            {'label':_('Can Add Users to Role'), 'permission': ('add_user_to_role', 'permafrost', 'permafrostrole')},
        ],
        'required': [
            {'label':_('Can add Role'), 'permission': ('add_permafrostrole', 'permafrost', 'permafrostrole')},
        ],
    },
}
```

This would be added to your Django `settings.py` file (or, at least, included into).  

In the above, we define the User category, give it the localizable label of "User" and provide two permissions in the "Natural Key" format (since PKs can be unreliable with permissions), the first is optional and the second is required.

There is also an access_level setting to help make sorting access levels more easily.

## Recommendations

It is recommended that you update your code to use PermafrotRole's built-in functions to add users and permissions.  They add an extra level of checking to make sure the permissions passed in are allowed by the PERMAFROST_CATEGORIES configuration.

For example, permissions on a Group:
```python
group.permissions.set([permission_list])
group.permissions.add(permission, permission, ...)
group.permissions.remove(permission, permission, ...)
group.permissions.clear()
```

Can be replaced with:
```python
PermafrostRole.permissions_set([permission_list])
PermafrostRole.permissions_add(permission, permission, ...)
PermafrostRole.permissions_remove(permission, permission, ...)
PermafrostRole.permissions_clear()
```


## Convenience tools
There is a tool to help the developer list out the permissions available in the format permafrost expects.

```shell
> ./manage permlist
```

using the command will produce a list like this

```shell
> ./manage.py permlist

Permlist formatted for your PermafrostRoles configuration
{'label':_('Can add email address'), 'permission': ('add_emailaddress', 'account', 'emailaddress')},
{'label':_('Can change email address'), 'permission': ('change_emailaddress', 'account', 'emailaddress')},
{'label':_('Can delete email address'), 'permission': ('delete_emailaddress', 'account', 'emailaddress')},
...
```

Each line can be copied into the PERMAFROST_CATEGORIES config in the correct format.

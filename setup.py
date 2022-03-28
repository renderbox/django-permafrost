# --------------------------------------------
# Copyright 2020, Grant Viklund
# @Author: Grant Viklund
# @Date:   2020-01-08 12:34:05
# --------------------------------------------

from os import path
from setuptools import setup, find_packages

from permafrost.__version__ import VERSION

readme_file = path.join(path.dirname(path.abspath(__file__)), 'README.md')

try:
    from m2r import parse_from_file
    long_description = parse_from_file(readme_file)     # Convert the file to RST for PyPI
except ImportError:
    # m2r may not be installed in user environment
    with open(readme_file) as f:
        long_description = f.read()

package_metadata = {
    'name': 'django-permafrost',
    'description': 'Adds Client Definable Permissions to Django',
    'version': VERSION,
    'long_description': long_description,
    'url': 'https://github.com/renderbox/django-permafrost/',
    'author': 'Grant Viklund',
    'author_email': 'renderbox@gmail.com',
    'license': 'MIT license',
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    'keywords': ['django', 'app'],
}

setup(
    **package_metadata,
    packages=find_packages(),
    package_data={'permafrost': ['*.html', 'management/commands/*.py', 'templates/permafrost/*.html', 'templates/permafrost/admin/*.html']},
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        'Django>=3.0,<4.1',
        'jsonfield',
    ],
    extras_require={
        'dev': [                            # Packages needed by developers
            'django-crispy-forms',
            'django-allauth',
            'django-extensions',
            'django-rest-framework',
        ],
        'test': [],                         # Packages needed to run tests
        'prod': [],                         # Packages needed to run in the deployment
        'build': [                          # Packages needed to build the package
            'setuptools',
            'wheel',
            'twine',
            'mistune<2.0.0',
            'm2r',
        ],
        'docs': [                           # Packages needed to generate docs
            'recommonmark',
            'm2r',
            'django-extensions',
            'coverage',
            'Sphinx',
            'rstcheck',
            'sphinx-rtd-theme',  # Assumes a Read The Docs theme for opensource projects
        ],
    }
)
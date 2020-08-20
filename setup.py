# --------------------------------------------
# Copyright 2020, Grant Viklund
# @Author: Grant Viklund
# @Date:   2020-01-08 12:34:05
# --------------------------------------------

from os import path
from setuptools import setup, find_packages
from m2r import parse_from_file

# file_path = path.abspath(path.dirname(__file__))

# with open(path.join(file_path, 'README.md'), encoding='utf-8') as f:
#     long_description = parse_from_file('markdown_file.md')f.read()

readme_file = path.join(path.dirname(path.abspath(__file__)), 'README.md')

try:
    from m2r import parse_from_file
    long_description = parse_from_file(readme_file)
except ImportError:
    # m2r may not be installed in user environment
    with open(readme_file) as f:
        long_description = f.read()


package_metadata = {
    'name': 'django-permafrost',
    'version': '0.2.0',
    'description': 'Adds Client Definable Permissions to Django',
    'long_description': long_description,
    'url': 'https://github.com/renderbox/django-permafrost/',
    'author': 'Grant Viklund',
    'author_email': 'renderbox@gmail.com',
    'license': 'MIT license',
    'classifiers': [
        'Development Status :: 2 - Pre-Alpha',
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
    package_data={'permafrost': ['*.html', 'management/commands/*.py', 'templates/permafrost/admin/*.html']},
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        'Django>=2.2',
        'djangorestframework',
        'jsonfield',
    ],
    extras_require={
        'dev': [],
        'test': [],
        'prod': [],
        'build': [
            'setuptools',
            'wheel',
            'twine',
            'm2r',
        ],
        'docs': [
            'coverage',
            'Sphinx',
            'sphinx-rtd-theme',
            'm2r',
        ],
    }
)
# --------------------------------------------
# Copyright 2020, Grant Viklund
# @Author: Grant Viklund
# @Date:   2020-01-08 12:34:05
# --------------------------------------------

from os import path
from setuptools import setup, find_packages

file_path = path.abspath(path.dirname(__file__))

with open(path.join(file_path, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

package_metadata = {
    'name': 'django-permafrost',
    'version': '0.1.6',
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
    package_data={'permafrost': ['*.html', 'management/commands/*.py']},
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        'Django>=2.2,<2.3',
    ],
    extras_require={
        'dev': [],
        'test': [],
        'prod': [],
        'build': [
            'setuptools',
            'wheel',
            'twine',
        ],
        'docs': [
            'coverage',
            'Sphinx',
            'sphinx-rtd-theme',
        ],
    }
)
import os

from setuptools import setup

import auditlog

# Readme as long description
with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as readme_file:
    long_description = readme_file.read()

setup(
    name='django-auditlog',
    version=auditlog.__version__,
    packages=['auditlog', 'auditlog.migrations', 'auditlog.management', 'auditlog.management.commands'],
    url='https://github.com/jjkester/django-auditlog',
    license='MIT',
    author='Jan-Jelle Kester',
    description='Audit log app for Django',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'django-jsonfield>=1.0.0',
        'python-dateutil>=2.6.0'
    ],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
    ],
)

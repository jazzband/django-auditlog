import os

from setuptools import setup

# Readme as long description
with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as readme_file:
    long_description = readme_file.read()

setup(
    name='django-auditlog',
    use_scm_version={"version_scheme": "post-release"},
    setup_requires=["setuptools_scm"],
    packages=['auditlog', 'auditlog.migrations', 'auditlog.management', 'auditlog.management.commands'],
    url='https://github.com/jazzband/django-auditlog',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
    ],
)

from distutils.core import setup

from setuptools import find_packages

setup(
    name='django-auditlog',
    version='0.4.5',
    packages=find_packages(where='src', exclude=['*tests*', 'runtests']),
    package_dir={'': 'src'},
    url='https://github.com/jjkester/django-auditlog',
    license='MIT',
    author='Jan-Jelle Kester',
    description='Audit log app for Django',
    install_requires=[
        'django-jsonfield>=1.0.0',
        'python-dateutil==2.6.0'
    ],
    zip_safe=False
)

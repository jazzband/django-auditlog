from distutils.core import setup

setup(
    name='django-auditlog',
    version='1.0.0',
    packages=['auditlog', 'auditlog.migrations', 'auditlog.management', 'auditlog.management.commands'],
    package_dir={'': 'src'},
    url='https://github.com/darwin-homes/django-auditlog',
    license='MIT',
    author='Darwin Homes',
    description='Audit log app for Django',
    install_requires=[
        'django-jsonfield>=1.0.0',
        'python-dateutil==2.7.5'
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

from distutils.core import setup

setup(
    name='django-auditlog',
    version='0.3.2',
    packages=['auditlog', 'auditlog.migrations'],
    package_dir={'': 'src'},
    url='https://github.com/jjkester/django-auditlog',
    license='MIT',
    author='Jan-Jelle Kester',
    author_email='janjelle@jjkester.nl',
    description='Audit log app for Django',
    install_requires=[
        'Django>=1.7',
        'django-jsonfield>=0.9.13',
    ]
)

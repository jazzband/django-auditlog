from distutils.core import setup

setup(
    name='django-auditlog',
    version='0.2.1',
    packages=['auditlog',],
    package_dir={'': 'src'},
    url='https://github.com/jjkester/django-auditlog',
    license='MIT',
    author='Jan-Jelle Kester',
    author_email='janjelle@jjkester.nl',
    description='Audit log app for Django',
    install_requires=[
        'Django>=1.5',
        'django-jsonfield>=0.9.13'
    ]
)

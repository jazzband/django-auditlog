import os

from setuptools import setup

# Readme as long description
with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme_file:
    long_description = readme_file.read()

setup(
    name="django-auditlog",
    use_scm_version={"version_scheme": "post-release"},
    setup_requires=["setuptools_scm"],
    packages=[
        "auditlog",
        "auditlog.migrations",
        "auditlog.management",
        "auditlog.management.commands",
    ],
    url="https://github.com/jazzband/django-auditlog",
    project_urls={
        "Documentation": "https://django-auditlog.readthedocs.io",
        "Source": "https://github.com/jazzband/django-auditlog",
        "Tracker": "https://github.com/jazzband/django-auditlog/issues",
    },
    license="MIT",
    author="Jan-Jelle Kester",
    description="Audit log app for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    install_requires=["Django>=3.2", "python-dateutil>=2.7.0"],
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "License :: OSI Approved :: MIT License",
    ],
)

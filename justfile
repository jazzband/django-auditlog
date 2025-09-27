# Default recipe that lists all available commands
default:
    @just --list

# Install dependencies
install:
    pip install -e .

# Run tests
test:
    ./runtests.sh

# Extract translatable strings and create/update .po files for all languages
makemessages:
    #!/usr/bin/env bash
    cd auditlog
    django-admin makemessages --add-location=file -a --ignore=__pycache__ --ignore=migrations
    cd ..

# Compile all translation files (.po to .mo)
compilemessages:
    #!/usr/bin/env bash
    cd auditlog
    django-admin compilemessages
    cd ..

# Full i18n workflow: extract strings, compile messages
i18n:
    @just makemessages
    @just compilemessages

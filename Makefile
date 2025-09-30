# Django Auditlog Makefile

# Default target shows help
.DEFAULT_GOAL := help
.PHONY: help install test makemessages compilemessages create-locale i18n clean

# Variables
AUDITLOG_DIR := auditlog
 
install: ## Install dependencies
	pip install -e .
 
test: ## Run tests
	./runtests.sh
 
makemessages: ## Extract translatable strings and create/update .po files for all languages
	cd $(AUDITLOG_DIR) && \
	django-admin makemessages --add-location=file -a --ignore=__pycache__ --ignore=migrations
 
compilemessages: ## Compile all translation files (.po to .mo)
	cd $(AUDITLOG_DIR) && \
	django-admin compilemessages

create-locale: ## Create initial locale structure for a new language (requires LANG=<code>)
	@if [ -z "$(LANG)" ]; then \
		echo "Error: LANG parameter is required. Usage: make create-locale LANG=<language_code>"; \
		echo "Examples: make create-locale LANG=ko, make create-locale LANG=ja"; \
		exit 1; \
	fi
	mkdir -p $(AUDITLOG_DIR)/locale/$(LANG)/LC_MESSAGES
	cd $(AUDITLOG_DIR) && \
	django-admin makemessages --add-location=file -l $(LANG) --ignore=__pycache__ --ignore=migrations

i18n: makemessages compilemessages ## Full i18n workflow: extract strings, compile messages

clean: ## Clean compiled translation files (.mo files)
	find $(AUDITLOG_DIR)/locale -name "*.mo" -delete
 
help:  ## Help message for targets
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

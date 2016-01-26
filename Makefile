VIRTUAL_ENV = $(shell echo "$${VIRTUAL_ENV:-.env}")
MODULE = spacewalk_osad2

all: $(VIRTUAL_ENV)

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile

.PHONY: clean
# target: clean - Display callable targets
clean:
	rm -rf build/ dist/ docs/_build *.egg-info
	find $(CURDIR) -name "*.py[co]" -delete
	find $(CURDIR) -name "*.orig" -delete

# ==============
#  Bump version
# ==============

.PHONY: release
VERSION?=minor
# target: release - Bump version
release:
	@$(VIRTUAL_ENV)/bin/pip install bumpversion
	@$(VIRTUAL_ENV)/bin/bumpversion $(VERSION)
	@git checkout master
	@git merge develop
	@git checkout develop
	@git push origin develop master
	@git push --tags

.PHONY: minor
minor: release

.PHONY: patch
patch:
	@make release VERSION=patch

.PHONY: major
major:
	@make release VERSION=major

# ===============
#  Build package
# ===============

.PHONY: register
# target: register - Register module on PyPi
register:
	@$(VIRTUAL_ENV)/bin/python setup.py register

.PHONY: upload
# target: upload - Upload module on PyPi
upload: clean
	@$(VIRTUAL_ENV)/bin/pip install twine wheel
	@$(VIRTUAL_ENV)/bin/python setup.py sdist bdist_wheel
	@$(VIRTUAL_ENV)/bin/twine upload dist/*
	@$(VIRTUAL_ENV)/bin/pip install -e $(CURDIR)

# =============
#  Development
# =============

$(VIRTUAL_ENV): requirements.txt
	[ -d $(VIRTUAL_ENV) ] || virtualenv --no-site-packages $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install -r requirements.txt
	@touch $(VIRTUAL_ENV)

$(VIRTUAL_ENV)/bin/py.test: $(VIRTUAL_ENV) requirements-tests.txt
	@$(VIRTUAL_ENV)/bin/pip install -r requirements-tests.txt
	@touch $(VIRTUAL_ENV)/bin/py.test

$(VIRTUAL_ENV)/bin/pylama: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install pylama
	@touch $(VIRTUAL_ENV)/bin/pylama

.PHONY: test
# target: test - Run tests
test: $(VIRTUAL_ENV)/bin/py.test
	@$(VIRTUAL_ENV)/bin/py.test tests

.PHONY: t
t: test

.PHONY: audit
# target: audit - Audit code
audit: $(VIRTUAL_ENV)/bin/pylama
	@$(VIRTUAL_ENV)/bin/pylama $(MODULE)

build:
	docker build -t horneds/spacewalk_osad $(CURDIR)

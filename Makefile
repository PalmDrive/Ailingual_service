project := xiaobandeng

flake8 := flake8
pytest := PYTHONDONTWRITEBYTECODE=1 py.test --tb short \
	--cov-config .coveragerc --cov $(project) \
	--async-test-timeout=1 --timeout=30 tests

html_report := --cov-report html
test_args := --cov-report term-missing

.DEFAULT_GOAL := test-lint

env/bin/activate:
	virtualenv env

env_install: env/bin/activate
	./env/bin/pip install -r requirement.txt
	./env/bin/python setup.py develop

.PHONY: tox_install
tox_install:
	pip install -r requirement.txt
	python setup.py develop

.PHONY: install
install: clean
ifdef TOX_ENV
	make tox_install
else
	make env_install
endif

.PHONY: test
test: clean
	$(pytest) $(test_args)

.PHONY: clean
clean:
	rm -rf dist/
	rm -rf build/
	@find $(project) tests -name "*.pyc" -delete

.PHONY: lint
lint: sort
	@$(flake8) $(project) tests examples setup.py

.PHONY: sort
sort:
	isort -sl -rc xiaobandeng

.PHONY: test-lint
test-lint: test lint

.PHONY: docs
docs:
	make -C docs html

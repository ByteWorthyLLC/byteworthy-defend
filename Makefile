.PHONY: test install-dev doctor docs-validate

install-dev:
	python -m pip install --upgrade pip
	pip install -e '.[dev]'

test:
	pytest

doctor:
	bw-defend doctor --json

docs-validate:
	./scripts/validate-docs.sh

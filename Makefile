.PHONY: test install-dev doctor docs-validate linux-gate docker-build docker-gate docker-shell

install-dev:
	python -m pip install --upgrade pip
	pip install -e '.[dev]'

test:
	pytest

doctor:
	bw-defend doctor --strict --json

docs-validate:
	./scripts/validate-docs.sh

linux-gate:
	./scripts/linux-gate.sh

docker-build:
	docker build -t byteworthy-defend:linux-gate .

docker-gate:
	docker compose run --rm linux-gate

docker-shell:
	docker compose run --rm linux-shell

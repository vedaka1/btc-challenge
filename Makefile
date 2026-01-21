DC = docker compose
DEV = docker-compose.dev.yaml
DC_DEV = $(DC) -f $(CURDIR)/.ci/docker-compose.yaml \
		--project-directory . \
		--env-file .env.production

local:
	PYTHONPATH=. .ci/entrypoint.sh

dev:
	$(DC_DEV) up -d

restart:
	$(DC_DEV) restart $(cont)
.PHONY: local
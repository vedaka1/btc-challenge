DC = docker compose
DEV = docker-compose.dev.yaml
DC_DEV = $(DC) -f $(CURDIR)/.ci/docker-compose.yaml \
		--project-directory . \
		--env-file .env.production

local:
	PYTHONPATH=. .ci/entrypoint.sh

dev:
	$(DC_DEV) up -d --build $(cont)

restart:
	$(DC_DEV) restart $(cont)

logs:
	$(DC_DEV) logs $(cont) --tail=500

down:
	$(DC_DEV) down

shell:
	$(DC_DEV) exec -it btc-challenge bash

sqlite:
	$(DC_DEV) exec -it btc-challenge sqlite3 app.db

.PHONY: local
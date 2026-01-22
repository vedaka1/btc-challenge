FROM python:3.12.12-trixie
COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

RUN pip install --upgrade pip
COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --no-editable

    
COPY btc_challenge/ ./btc_challenge
COPY .env.production alembic.ini ./
COPY alembic/ ./alembic/
COPY ./.ci/entrypoint.sh /app/.ci/entrypoint.sh

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

RUN chmod +x /app/.ci/entrypoint.sh
CMD ["/bin/bash", "/app/.ci/entrypoint.sh"]

FROM python:3.12-slim

ARG UID=1000
ARG GID=1000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    PATH="/home/developer/.local/bin:${PATH}"

# Bash and CA certificates. The project is bind-mounted at /app, so PYTHONPATH
# makes the mounted source take precedence over the copy installed at build time.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# set internal docker user to same userid/groupid as your host-system user
RUN groupadd --gid ${GID} developer \
    && useradd \
        --uid ${UID} \
        --gid ${GID} \
        --create-home \
        --shell /bin/bash \
        developer

WORKDIR /app

# grant access to alle project files
COPY --chown=developer:developer pyproject.toml README.md ./
COPY --chown=developer:developer src/ ./src/

USER developer

# install alle developer tools from requirements
RUN python -m pip install --user ".[dev]"

CMD ["sleep", "infinity"]

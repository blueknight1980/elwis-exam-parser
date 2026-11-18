#!/bin/bash
# .docker/down.sh
docker compose down

# mit -v wird die DB gelöscht
# docker compose --env-file ../.env down -v

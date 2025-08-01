#!/bin/bash

set -e
 
# docker-compose command detect
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found. Please install Docker Desktop or docker-compose."
    exit 1
fi

# start PostgreSQL container
echo "Starting PostgreSQL container"
$COMPOSE_CMD up -d postgres

# wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
  if $COMPOSE_CMD exec postgres pg_isready -U postgres >/dev/null 2>&1; then
    echo "PostgreSQL is ready!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "PostgreSQL failed to start after 30 attempts"
    exit 1
  fi
  echo "PostgreSQL is unavailable - sleeping (attempt $i/30)"
  sleep 1
done

# set environment variables
export TEST_DB_HOST=localhost
export TEST_DB_USER=postgres 
export TEST_DB_PASS=postgres
export TEST_DB_NAME=postgres
export TEST_DB_PORT=5432

echo "Running tox with PostgreSQL"

# run tox
tox -v "$@"

echo "Tests completed."
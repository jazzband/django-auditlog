#!/usr/bin/env bash

# Run tests against all supported databases
set -e

# Default settings
export TEST_DB_USER=${TEST_DB_USER:-testuser}
export TEST_DB_PASS=${TEST_DB_PASS:-testpass}
export TEST_DB_HOST=${TEST_DB_HOST:-127.0.0.1}
export TEST_DB_NAME=${TEST_DB_NAME:-auditlog}

# Cleanup on exit 
trap 'docker compose -f auditlog_tests/docker-compose.yml down -v --remove-orphans 2>/dev/null || true' EXIT

echo "Starting containers..."
docker compose -f auditlog_tests/docker-compose.yml up -d

echo "Waiting for databases..."
echo "Waiting for PostgreSQL..."
until docker compose -f auditlog_tests/docker-compose.yml exec postgres pg_isready -U ${TEST_DB_USER} -d auditlog >/dev/null 2>&1; do
    sleep 1
done

echo "Waiting for MySQL..."

until docker compose -f auditlog_tests/docker-compose.yml exec mysql mysqladmin ping -h 127.0.0.1 -u ${TEST_DB_USER} --password=${TEST_DB_PASS} --silent >/dev/null 2>&1; do
    sleep 1
done
echo "Databases ready!"

# Run tests for each database
for backend in sqlite3 postgresql mysql; do
    echo "Testing $backend..."
    export TEST_DB_BACKEND=$backend
    case $backend in
        postgresql) export TEST_DB_PORT=5432 ;;
        mysql) export TEST_DB_PORT=3306;;
        sqlite3) unset TEST_DB_PORT ;;
    esac
    tox
done

echo "All tests completed!"

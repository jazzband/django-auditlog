#!/usr/bin/env bash
set -e

mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<-EOSQL
  GRANT ALL PRIVILEGES ON test_auditlog.* to '$MYSQL_USER';
EOSQL

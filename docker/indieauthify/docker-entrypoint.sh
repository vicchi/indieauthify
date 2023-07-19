#!/bin/bash

if [[ ! -r "${TOKEN_DB_PATH}" ]]; then
    echo "Bootstrapping ${TOKEN_DB_PATH}"
    sqlite3 -batch "${TOKEN_DB_PATH}" < /service/init-tokendb.sql
else
    echo "${TOKEN_DB_PATH} found; skipping bootstrap"
fi
exec "$@"

#!/bin/sh
set -e

echo "Waiting for Postgres..."
until pg_isready -h db -p 5432 -U jobbot; do
  sleep 2
done

exec "$@"



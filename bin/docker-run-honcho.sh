#!/usr/bin/env bash
#   Shorthand to migrate and run honcho in docker

# If DB_HOST is set, wait for DB port
if [ -n "$DB_HOST" ]; then
    ./bin/docker-wait.sh --timeout=30 "$DB_HOST:${DB_PORT:-5432}" -- echo "Database is ready"
fi

cd tabbycat

# Migrate (can't do it during build; no db connnection)
python ./manage.py migrate --no-input

# Needed to ensure daphne works properly
rm -f /tmp/asgi.socket /tmp/asgi.socket.lock

# Run honcho
cd ..
honcho -f ./ProcfileMulti.docker start

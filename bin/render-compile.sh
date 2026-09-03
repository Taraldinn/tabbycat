#!/usr/bin/env bash
# exit on error
set -o errexit

echo "-----> Install Python dependencies"
python -m pip install pipenv
pipenv install --system

if [ "${IS_WORKER:-0}" = "1" ]; then
    echo "-----> Worker build complete (skipping migrations & asset compilation)"
    exit 0
fi

echo "-----> Running database migrations"
cd ./tabbycat/
python manage.py migrate --noinput

echo "-----> Creating DB cache table (skipped if USE_REDIS=1)"
if [ "${USE_REDIS:-0}" = "0" ]; then
    python manage.py createcachetable
fi

echo "-----> Running dynamic preferences checks"
python manage.py checkpreferences

echo "-----> Building frontend assets"
cd ..
npm install
npm run build

echo "-----> Collecting static files"
cd ./tabbycat/
python manage.py collectstatic --noinput

echo "-----> Build complete"

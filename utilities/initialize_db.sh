#!/bin/bash

set -e

# Test for python via virtualenv
python --version 2>&1 > /dev/null

pushd .. 2>&1 > /dev/null

if [[ -f "db.sqlite3" ]]; then
    echo Found an old database, removing it now...
    rm db.sqlite3
fi

# Initialize the database
echo Initializing database
python manage.py migrate

# Initialize users
echo Creating initial users
python manage.py shell < ./utilities/create_users.py

popd 2>&1 > /dev/null

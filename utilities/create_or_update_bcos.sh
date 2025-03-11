#!/bin/bash

set -e

# Test for python via virtualenv
python --version 2>&1 > /dev/null

pushd .. 2>&1 > /dev/null

# Update or create BCO data descriptors in the DB
echo Updating or creating BCOs
python manage.py shell < ./utilities/create_or_update_bcos.py

popd 2>&1 > /dev/null
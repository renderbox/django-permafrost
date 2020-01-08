#!/bin/bash

#Every build wants this folder, so make it here
mkdir -p $DJANGO_LOG

# Update all Python dependencies
cd ..
yes | pip3 install --no-warn-script-location --upgrade --trusted-host pip.whitemoonlabs.com \
  --extra-index-url http://pip.whitemoonlabs.com/ -e .['build']; PIP_STATUS=$?

# Update database
cd develop
python3 manage.py migrate; MIGRATE_STATUS=$?

EXIT_ERRORS=0
if [ $PIP_STATUS -ne 0 ]; then
  echo "Pip dependency install failed with status $PIP_STATUS"
  EXIT_ERRORS=$(( $PIP_STATUS > $EXIT_ERRORS ? $PIP_STATUS : $EXIT_ERRORS ))
fi
if [ $MIGRATE_STATUS -ne 0 ]; then 
  echo "Database migrations failed with status $MIGRATE_STATUS"
  EXIT_ERRORS=$(( $MIGRATE_STATUS > $EXIT_ERRORS ? $MIGRATE_STATUS : $EXIT_ERRORS ))
fi

cd ../setup

exit $EXIT_ERRORS
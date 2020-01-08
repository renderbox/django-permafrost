#!/bin/bash

# Test for migration gaps
cd ../develop
python3 manage.py makemigrations --check --dry-run; NEED_MIGRATIONS=$?

# Run Django tests
python3 manage.py test; PY_TEST_STATUS=$?

EXIT_ERRORS=0
if [ $NEED_MIGRATIONS -ne 0 ]; then 
  echo "Migrations are needed, status $NEED_MIGRATIONS"
  EXIT_ERRORS=$(( $NEED_MIGRATIONS > $EXIT_ERRORS ? $NEED_MIGRATIONS : $EXIT_ERRORS ))
fi
if [ $PY_TEST_STATUS -ne 0 ]; then 
  echo "Python tests failed with status $PY_TEST_STATUS"
  EXIT_ERRORS=$(( $PY_TEST_STATUS > $EXIT_ERRORS ? $PY_TEST_STATUS : $EXIT_ERRORS ))
fi

cd ../setup
exit $EXIT_ERRORS
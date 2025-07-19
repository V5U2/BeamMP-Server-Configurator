#!/bin/bash

ACCESS_LOG=${GUNICORN_ACCESS_LOG:--}
exec gunicorn -w 1 -b 0.0.0.0:5000 --access-logfile "$ACCESS_LOG" app:app 
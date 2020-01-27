#!/bin/bash

gunicorn -w5 -b 0.0.0.0:8080 app:app --daemon --access-logfile access.log --error-logfile error.log -t 3600


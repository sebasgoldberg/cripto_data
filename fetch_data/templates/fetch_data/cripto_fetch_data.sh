#!/usr/bin/env bash

. {{virtualenv_path}}/bin/activate

while true;
do
    python {{django_project_path}}/manage.py quote_latest
    sleep 5m
done;
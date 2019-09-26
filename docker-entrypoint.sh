#!/bin/bash

uwsgi --http 0.0.0.0:9000 --wsgi-file app.py --callable app --processes 4 --threads 2
#!/bin/bash

apt-get update
APT_GET="apt-get install -y --allow-unauthenticated"

$APT_GET locales python3.8 python3-pip
pip3 install -r /app/requirements.txt

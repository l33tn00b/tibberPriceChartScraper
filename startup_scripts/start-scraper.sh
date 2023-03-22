#!/usr/bin/env bash

echo "Starting scrape script..."

# we'd love to be able to wait for having all other processes up.
# https://github.com/Supervisor/supervisor/issues/122
while [[ $(ps -aux | grep "/usr/bin/fluxbox") == "" ]];
do
    echo "Waiting for fluxbox to come up to start scrape script..."
    sleep 2s
    if [[ $(ps -aux | grep "/usr/bin/fluxbox") != "" ]]; then
        echo "fluxbox seems to be up..."
        ps -aux | grep "/usr/bin/fluxbox"
    fi
done

# fluxbox seems to be up...
# continue
python3 /home/seluser/scripts/scrape_firefox.py

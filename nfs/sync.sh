#!/bin/bash -e

sudo -E rsync -t -r --delete ~/setup-scripts/ /var/nfs/exports/setup-scripts

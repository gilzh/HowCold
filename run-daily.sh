#!/bin/bash
set -e
cd /Users/gilles/Coding/HowCold
node fetch.js
git add temperatures.csv
git commit -m "Daily HowCold update - $(date +%Y-%m-%d)"
git push

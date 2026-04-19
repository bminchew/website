#!/bin/bash

cd "$(dirname "$0")"

git add -A
git commit -m "update site $(date +%Y-%m-%d)"
git push

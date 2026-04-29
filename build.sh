#!/bin/bash

cd "$(dirname "$0")"
python3 build_research_hub.py

cd cv
./build_cv_caltech.sh

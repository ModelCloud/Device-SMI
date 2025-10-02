#!/bin/bash

cd "$(dirname "$0")" || exit

# force ruff/isort to be same version as setup.py
pip install -U ruff==0.9.6 isort==6.0.0

ruff check ../device_smi ../tests --fix --unsafe-fixes
ruff_status=$?

isort -l 119 -e ../

# Exit with the status code of ruff check
exit $ruff_status
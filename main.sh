#!/bin/bash

CURR_DIR="$(dirname "$(realpath "$0")")"

cleanup() {
    echo "deactivating venv"
    deactivate

    echo "all done :)"
}

trap cleanup EXIT

echo "main.sh called, current time is: $(date)"

echo "navigating to directory $CURR_DIR"
cd "$CURR_DIR" || exit

echo "activating venv"
source venv/bin/activate

echo "running main.py"
python3 main.py

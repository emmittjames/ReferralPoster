#!/bin/bash

cleanup() {
    echo "deactivating venv"
    deactivate

    echo "all done :)"
}

trap cleanup EXIT

echo "main.sh called, current time is: $(date)"

echo "activating venv"
source venv/bin/activate

echo "running main.py"
python3 main.py

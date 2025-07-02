#!/bin/bash

# start_client.sh
# This script starts the client application for the Progetto Laboratorio D'Informatica Applicata.

# Change to the directory where this script is located.
# This allows the script to be run from anywhere, as it will always operate relative to its own location.
# The script assumes it is located in the 'client' directory of the project.
cd "$(dirname "$0")/client"

# Ensure the script is run from the client directory
export PYTHONPATH=.

# Start the client application
python main.py

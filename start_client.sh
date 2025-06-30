#!/bin/bash
cd "$(dirname "$0")/client"

# Assicurati che Python veda 'client/' come root dei moduli
export PYTHONPATH=.

# Avvia il main
python main.py

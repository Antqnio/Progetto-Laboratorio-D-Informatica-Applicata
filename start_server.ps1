# start_server.ps1

# Create the virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    uv venv
}

# Activate the virtual environment
. .\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r .\server\server_requirements.txt

# Run server.py in the same terminal
python .\server\server.py

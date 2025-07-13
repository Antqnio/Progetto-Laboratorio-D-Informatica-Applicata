# start_server.ps1

# Configure the Python version or path here
$py = "python3.11"
# (Alternatively: $py = "C:\Path\To\Python311\python.exe")

# Set UV_PYTHON to specify Python version
$env:UV_PYTHON = $py

# Create the virtual environment if it doesn't exist
if (!(Test-Path ".venv")) {
    uv venv --python $py
}

# Activate the virtual environment
. .\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r .\server\server_requirements.txt

# Run server.py in the same terminal
python .\server\server.py

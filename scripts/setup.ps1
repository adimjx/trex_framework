# Define helper functions with color and symbols
function Info($msg)    { Write-Host "==> $msg" -ForegroundColor Cyan }
function Success($msg) { Write-Host "✔ $msg" -ForegroundColor Green }
function Warn($msg)    { Write-Host "! $msg" -ForegroundColor Yellow }
function ErrorOut($msg) {
    Write-Host "✖ $msg" -ForegroundColor Red
    exit 1
}

# Step 1: Check if Python is installed
Info "Checking for Python..."

$python = Get-Command python -ErrorAction SilentlyContinue
$py = Get-Command py -ErrorAction SilentlyContinue

if ($py) {
    Success "Python found as 'py'"
} elseif ($python) {
    Success "Python found as 'python'"
    Set-Alias -Name py -Value python
} else {
    ErrorOut "Python is not installed. Please install Python and try again."
}

# Step 2: Create virtual environment and activate it
Info "Creating virtual environment..."
py -m venv .venv

if (-Not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    ErrorOut "Virtual environment activation script not found. Something went wrong."
}

Info "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1
Success "Virtual environment activated."

# Step 3: Install Poetry and dependencies
Info "Installing Poetry..."
pip install poetry

Info "Installing project dependencies with Poetry..."
poetry install

Success "Setup complete!"

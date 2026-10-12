$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$serverDirectory = Join-Path $projectRoot 'server'
$dashboardDirectory = Join-Path $projectRoot 'dashboard'
$pythonEnvironment = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path (Join-Path $serverDirectory 'server_runner.py'))) {
    throw "Backend runner not found under '$serverDirectory'."
}

if (-not (Test-Path (Join-Path $dashboardDirectory 'package.json'))) {
    throw "Dashboard package.json not found under '$dashboardDirectory'."
}

if (-not (Test-Path (Join-Path $dashboardDirectory 'node_modules'))) {
    throw "Dashboard dependencies are missing. Run 'npm install' in '$dashboardDirectory' first."
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'npm was not found. Install Node.js and npm, then open a new PowerShell window.'
}

if (-not (Test-Path $pythonEnvironment)) {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $python) {
        throw 'Python was not found. Install Python or create the project .venv first.'
    }
    $pythonEnvironment = $python.Source
}

$shell = (Get-Process -Id $PID).Path
$serverPath = $serverDirectory.Replace("'", "''")
$dashboardPath = $dashboardDirectory.Replace("'", "''")
$pythonPath = $pythonEnvironment.Replace("'", "''")

$serverCommand = "Set-Location -LiteralPath '$serverPath'; `$Host.UI.RawUI.WindowTitle = 'Secure Session Manager - Server'; & '$pythonPath' server_runner.py"
$dashboardCommand = "Set-Location -LiteralPath '$dashboardPath'; `$Host.UI.RawUI.WindowTitle = 'Secure Session Manager - Dashboard'; npm run dev"

Start-Process -FilePath $shell -WorkingDirectory $serverDirectory -ArgumentList "-NoExit -NoProfile -ExecutionPolicy Bypass -Command `"$serverCommand`""
Start-Process -FilePath $shell -WorkingDirectory $dashboardDirectory -ArgumentList "-NoExit -NoProfile -ExecutionPolicy Bypass -Command `"$dashboardCommand`""

Write-Host 'Backend and dashboard are starting in separate PowerShell windows.'
Write-Host 'Dashboard: http://localhost:3000 (sign in with admin / admin)'
Write-Host 'Backend:   http://localhost:8443'

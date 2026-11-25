<#
.SYNOPSIS
    Prepares a Windows computer to run EstateAI: tools, dependencies, configuration and checks.

.DESCRIPTION
    1. Installs Git, Node.js (LTS) and uv with winget when they are missing or too old.
    2. Installs the exact frontend and backend dependencies from the lock files.
    3. Creates backend/.env from backend/.env.example when it does not exist.
    4. Checks the database connection, runs the tests and builds the frontend.

    Running it again is safe: installed tools are kept and only missing parts are added.

.PARAMETER SkipChecks
    Installs everything but skips the database check, the tests and the build.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File setup.ps1
#>
param(
    [switch]$SkipChecks
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot 'frontend'
$BackendDir = Join-Path $ProjectRoot 'backend'
$EnvFile = Join-Path $BackendDir '.env'

# The Python version the backend is developed and tested with. uv downloads it when needed.
$PythonVersion = '3.14'

$Results = New-Object System.Collections.Generic.List[object]

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "> $Message" -ForegroundColor Cyan
}

function Add-Result([string]$Name, [string]$Status, [string]$Detail) {
    $Results.Add([pscustomobject]@{ Check = $Name; Status = $Status; Detail = $Detail })
    $colour = @{ OK = 'Green'; WARNING = 'Yellow'; FAILED = 'Red'; SKIPPED = 'DarkGray' }[$Status]
    Write-Host "  [$Status] $Name $Detail" -ForegroundColor $colour
}

function Test-Command([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# Programs installed by winget update PATH in the registry; this session reads it again.
function Update-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

function Install-WithWinget([string]$PackageId, [string]$DisplayName, [string]$ManualUrl) {
    if (-not (Test-Command 'winget')) {
        throw "$DisplayName is missing and winget is not available. Install it from $ManualUrl, then run this script again."
    }
    Write-Host "  Installing $DisplayName with winget. Windows may ask for permission."
    & winget install --id $PackageId --exact --source winget --silent `
        --accept-package-agreements --accept-source-agreements | Out-Host
    # winget returns a non-zero code when an older version is already installed.
    if ($LASTEXITCODE -ne 0) {
        & winget upgrade --id $PackageId --exact --source winget --silent `
            --accept-package-agreements --accept-source-agreements | Out-Host
    }
    Update-SessionPath
}

# Angular 22 supports Node.js ^22.22.3, ^24.15.0 and >=26.0.0 (see @angular/core engines).
function Test-SupportedNode([version]$Version) {
    if ($Version.Major -ge 26) { return $true }
    if ($Version.Major -eq 24) { return $Version -ge [version]'24.15.0' }
    if ($Version.Major -eq 22) { return $Version -ge [version]'22.22.3' }
    return $false
}

function Get-NodeVersion {
    if (-not (Test-Command 'node')) { return $null }
    return [version]((& node --version).Trim().TrimStart('v'))
}

# Runs a program inside a folder and reports whether it exited successfully. Its output goes to
# the console, so that it does not become part of the function's return value.
function Invoke-InFolder([string]$Folder, [scriptblock]$Command) {
    Push-Location $Folder
    try {
        & $Command | Out-Host
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        Pop-Location
    }
}

Write-Host 'EstateAI setup' -ForegroundColor White
Write-Host "Project folder: $ProjectRoot"

try {
    Write-Step 'Tools'

    if (-not (Test-Command 'git')) {
        Install-WithWinget 'Git.Git' 'Git' 'https://git-scm.com/download/win'
    }
    if (Test-Command 'git') {
        Add-Result 'Git' 'OK' ((& git --version) -replace 'git version ', '')
    }
    else {
        Add-Result 'Git' 'WARNING' 'installed; open a new terminal if it is not found'
    }

    $nodeVersion = Get-NodeVersion
    if ($null -eq $nodeVersion -or -not (Test-SupportedNode $nodeVersion)) {
        if ($null -ne $nodeVersion) {
            Write-Host "  Node.js $nodeVersion is not supported by Angular 22."
        }
        Install-WithWinget 'OpenJS.NodeJS.LTS' 'Node.js LTS' 'https://nodejs.org'
        $nodeVersion = Get-NodeVersion
    }
    if ($null -eq $nodeVersion -or -not (Test-SupportedNode $nodeVersion)) {
        throw "Node.js $nodeVersion is still not supported. Remove other Node.js installations (for example nvm), install the LTS version from https://nodejs.org and run this script again."
    }
    Add-Result 'Node.js' 'OK' "v$nodeVersion"

    if (-not (Test-Command 'uv')) {
        Install-WithWinget 'astral-sh.uv' 'uv' 'https://docs.astral.sh/uv/getting-started/installation/'
    }
    if (-not (Test-Command 'uv')) {
        throw 'uv was installed but is not found yet. Open a new terminal and run this script again.'
    }
    Add-Result 'uv' 'OK' ((& uv --version) -replace '^uv ', '')

    Write-Step 'Frontend dependencies (npm ci, exact versions from package-lock.json)'
    # npm.cmd also works when PowerShell blocks the npm.ps1 wrapper.
    if (Invoke-InFolder $FrontendDir { & npm.cmd ci --no-audit --no-fund }) {
        Add-Result 'Frontend dependencies' 'OK' ''
    }
    else {
        throw 'npm ci failed. Check the messages above and your internet connection.'
    }

    Write-Step "Backend dependencies (uv sync, exact versions from uv.lock, Python $PythonVersion)"
    if (Invoke-InFolder $BackendDir { & uv sync --locked --python $PythonVersion }) {
        Add-Result 'Backend dependencies' 'OK' "Python $PythonVersion"
    }
    else {
        throw 'uv sync failed. Check the messages above and your internet connection.'
    }

    Write-Step 'Configuration'
    if (-not (Test-Path $EnvFile)) {
        Copy-Item (Join-Path $BackendDir '.env.example') $EnvFile
        Write-Host '  Created backend/.env from backend/.env.example.'
    }
    $envText = Get-Content $EnvFile -Raw
    $configurationComplete = $envText -notmatch '<project-ref>|<database-password>'
    if ($configurationComplete) {
        Add-Result 'backend/.env' 'OK' ''
    }
    else {
        Add-Result 'backend/.env' 'WARNING' 'fill in DATABASE_URL and SUPABASE_URL (copy your own .env file)'
    }

    Write-Step 'Checks'
    if ($SkipChecks) {
        Add-Result 'Checks' 'SKIPPED' 'run without -SkipChecks to verify the installation'
    }
    else {
        if ($configurationComplete) {
            if (Invoke-InFolder $BackendDir { & uv run python -m app.db.check_connection }) {
                Add-Result 'Database connection' 'OK' ''
            }
            else {
                Add-Result 'Database connection' 'FAILED' 'check DATABASE_URL and the internet connection'
            }
            if (Invoke-InFolder $BackendDir { & uv run pytest -q }) {
                Add-Result 'Backend tests' 'OK' ''
            }
            else {
                Add-Result 'Backend tests' 'FAILED' 'see the pytest output above'
            }
        }
        else {
            Add-Result 'Database connection' 'SKIPPED' 'backend/.env is not filled in'
            Add-Result 'Backend tests' 'SKIPPED' 'they use the database configured in backend/.env'
        }

        if (Invoke-InFolder $FrontendDir { & npx.cmd ng test --watch=false }) {
            Add-Result 'Frontend tests' 'OK' ''
        }
        else {
            Add-Result 'Frontend tests' 'FAILED' 'see the test output above'
        }
        if (Invoke-InFolder $FrontendDir { & npx.cmd ng build }) {
            Add-Result 'Frontend build' 'OK' ''
        }
        else {
            Add-Result 'Frontend build' 'FAILED' 'see the build output above'
        }
    }
}
catch {
    Add-Result 'Setup' 'FAILED' $_.Exception.Message
}

Write-Host ''
Write-Host 'Summary' -ForegroundColor White
$Results | Format-Table -AutoSize | Out-String | Write-Host

$failed = @($Results | Where-Object { $_.Status -eq 'FAILED' }).Count -gt 0
if ($failed) {
    Write-Host 'Setup is not complete. Fix the FAILED items above and run the script again.' -ForegroundColor Red
    exit 1
}

Write-Host 'EstateAI is ready. Start it in two terminals:' -ForegroundColor Green
Write-Host '  1. cd backend;  uv run uvicorn app.main:app --reload'
Write-Host '  2. cd frontend; npm.cmd start'
Write-Host 'Then open http://localhost:4200'
exit 0

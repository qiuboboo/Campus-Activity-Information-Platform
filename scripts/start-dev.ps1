param(
    [ValidateSet("mock", "docker")]
    [string]$Mode = "mock",
    [switch]$Install,
    [switch]$InitDb,
    [switch]$SeedDemo,
    [switch]$Stop,
    [switch]$ForcePorts
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$FrontendDir = Join-Path $RepoRoot "frontend"
$BackendDir = Join-Path $RepoRoot "backend"
$LogDir = Join-Path $RepoRoot ".dev-logs"
$PidDir = Join-Path $RepoRoot ".dev-pids"

function Write-Step($Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Warn($Message) {
    Write-Host "WARN: $Message" -ForegroundColor Yellow
}

function Write-Fail($Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Ensure-Directory($Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Get-Listeners($Port) {
    @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique)
}

function Stop-RecordedProcesses {
    if (-not (Test-Path $PidDir)) {
        Write-Warn "No recorded dev process directory found."
        return
    }

    Get-ChildItem -Path $PidDir -Filter "*.pid" | ForEach-Object {
        $processId = [int](Get-Content $_.FullName)
        $name = $_.BaseName
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Step "Stopping $name (PID $processId)"
            Stop-Process -Id $processId -Force
        }
        Remove-Item -LiteralPath $_.FullName -Force
    }
}

function Stop-RemainingPortListeners($Ports) {
    foreach ($port in $Ports) {
        $listeners = Get-Listeners $port
        if ($listeners.Count -eq 0) {
            continue
        }

        if (-not $ForcePorts) {
            Write-Warn "Port $port is still in use by PID(s): $($listeners -join ', '). Use -ForcePorts if you want the script to stop them."
            continue
        }

        foreach ($processId in $listeners) {
            Write-Warn "Stopping remaining process $processId on port $port because -ForcePorts was provided."
            Stop-Process -Id $processId -Force
        }
    }
}

function Record-PortListeners($Name, $Port) {
    Ensure-Directory $PidDir
    $listeners = Get-Listeners $Port
    foreach ($processId in $listeners) {
        Set-Content -Path (Join-Path $PidDir "$Name-port$Port-$processId.pid") -Value $processId
    }
}

function Clear-PortIfRequested($Port, $Label) {
    $listeners = Get-Listeners $Port
    if ($listeners.Count -eq 0) {
        return
    }

    if (-not $ForcePorts) {
        $details = $listeners -join ", "
        throw "$Label port $Port is already in use by PID(s): $details. Stop it first, run with -ForcePorts, or use scripts/start-dev.ps1 -Stop if it was started by this script."
    }

    foreach ($processId in $listeners) {
        Write-Warn "Stopping process $processId on port $Port because -ForcePorts was provided."
        Stop-Process -Id $processId -Force
    }
    Start-Sleep -Seconds 1
}

function Ensure-Command($Name, $Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $Hint"
    }
}

function Start-LoggedProcess($Name, $FilePath, $Arguments, $WorkingDirectory) {
    Ensure-Directory $LogDir
    Ensure-Directory $PidDir

    $stdout = Join-Path $LogDir "$Name.out.log"
    $stderr = Join-Path $LogDir "$Name.err.log"
    if (Test-Path $stdout) { Remove-Item -LiteralPath $stdout -Force }
    if (Test-Path $stderr) { Remove-Item -LiteralPath $stderr -Force }

    Write-Step "Starting $Name"
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru

    Set-Content -Path (Join-Path $PidDir "$Name.pid") -Value $process.Id
    Write-Host "    PID: $($process.Id)"
    Write-Host "    Logs: $stdout / $stderr"
}

function Ensure-FrontendDependencies {
    Ensure-Command "node" "Install Node.js 18+."
    Ensure-Command "npm.cmd" "Install Node.js 18+ and make sure npm is on PATH."

    if ($Install -or -not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Step "Installing frontend dependencies"
        Push-Location $FrontendDir
        try {
            npm install
        }
        finally {
            Pop-Location
        }
    }
}

function Start-FrontendDevServer {
    Clear-PortIfRequested 3000 "Vite"
    Start-LoggedProcess `
        -Name "frontend-vite" `
        -FilePath "npm.cmd" `
        -Arguments @("run", "dev", "--", "--host", "127.0.0.1") `
        -WorkingDirectory $FrontendDir
    Start-Sleep -Seconds 2
    Record-PortListeners "frontend-vite" 3000
}

function Start-MockBackend {
    Clear-PortIfRequested 5000 "Mock API"
    Start-LoggedProcess `
        -Name "frontend-mock" `
        -FilePath "node" `
        -Arguments @("mock/index.js") `
        -WorkingDirectory $FrontendDir
    Start-Sleep -Seconds 1
    Record-PortListeners "frontend-mock" 5000
}

function Start-DockerBackend {
    Ensure-Command "docker" "Install Docker Desktop and start it."
    Clear-PortIfRequested 5000 "Backend API"

    Write-Step "Starting Docker backend"
    Push-Location $BackendDir
    try {
        docker compose up -d --build postgres redis api worker
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose up failed. If it failed while pulling python:3.12-slim, configure a Docker mirror or retry after the network is stable."
        }

        if ($InitDb) {
            Write-Step "Initializing database"
            docker compose exec api flask --app wsgi init-db
        }
        if ($SeedDemo) {
            Write-Step "Seeding demo data"
            docker compose exec api flask --app wsgi seed-demo
        }
    }
    finally {
        Pop-Location
    }
}

try {
    if ($Stop) {
        Stop-RecordedProcesses
        Stop-RemainingPortListeners @(3000, 5000)
        Write-Host "Stopped recorded dev processes."
        exit 0
    }

    Ensure-FrontendDependencies

    if ($Mode -eq "mock") {
        Start-MockBackend
    }
    elseif ($Mode -eq "docker") {
        Start-DockerBackend
    }

    Start-FrontendDevServer
    Start-Sleep -Seconds 2

    Write-Host ""
    Write-Host "Frontend: http://127.0.0.1:3000" -ForegroundColor Green
    if ($Mode -eq "mock") {
        Write-Host "API:      http://127.0.0.1:5000 (Mock)" -ForegroundColor Green
    }
    else {
        Write-Host "API:      http://127.0.0.1:5000 (Docker backend)" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Stop local dev processes: powershell -ExecutionPolicy Bypass -File scripts/start-dev.ps1 -Stop"
    Write-Host "Logs are in: $LogDir"
}
catch {
    Write-Fail $_.Exception.Message
    exit 1
}

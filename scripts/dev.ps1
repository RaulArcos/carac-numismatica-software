# Development script for Carac project
# Run with: .\scripts\dev.ps1

param(
    [string]$Command = "help",
    [string]$Target = ""
)

function Show-Help {
    Write-Host "Carac Development Script" -ForegroundColor Green
    Write-Host "========================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\scripts\dev.ps1 <command> [target]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  install     - Install dependencies with Poetry" -ForegroundColor White
    Write-Host "  run         - Run the application" -ForegroundColor White
    Write-Host "  test        - Run tests" -ForegroundColor White
    Write-Host "  lint        - Run linting checks" -ForegroundColor White
    Write-Host "  format      - Format code" -ForegroundColor White
    Write-Host "  typecheck   - Run type checking" -ForegroundColor White
    Write-Host "  build       - Build executable with PyInstaller" -ForegroundColor White
    Write-Host "  clean       - Clean build artifacts" -ForegroundColor White
    Write-Host "  help        - Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev.ps1 install" -ForegroundColor White
    Write-Host "  .\scripts\dev.ps1 run" -ForegroundColor White
    Write-Host "  .\scripts\dev.ps1 test" -ForegroundColor White
    Write-Host "  .\scripts\dev.ps1 build" -ForegroundColor White
}

function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor Green
    poetry install --with dev,packaging
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}

function Run-Application {
    Write-Host "Running Carac application..." -ForegroundColor Green
    poetry run carac
}

function Run-Tests {
    Write-Host "Running tests..." -ForegroundColor Green
    if ($Target) {
        poetry run pytest $Target
    } else {
        poetry run pytest
    }
}

function Run-Linting {
    Write-Host "Running linting checks..." -ForegroundColor Green
    poetry run ruff check src/
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Linting passed!" -ForegroundColor Green
    } else {
        Write-Host "Linting failed!" -ForegroundColor Red
        exit 1
    }
}

function Format-Code {
    Write-Host "Formatting code..." -ForegroundColor Green
    poetry run ruff format src/
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Code formatted successfully!" -ForegroundColor Green
    } else {
        Write-Host "Code formatting failed!" -ForegroundColor Red
        exit 1
    }
}

function Run-TypeCheck {
    Write-Host "Running type checking..." -ForegroundColor Green
    poetry run mypy src/carac
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Type checking passed!" -ForegroundColor Green
    } else {
        Write-Host "Type checking failed!" -ForegroundColor Red
        exit 1
    }
}

function Build-Executable {
    Write-Host "Building executable..." -ForegroundColor Green
    poetry run pyinstaller packaging/pyinstaller/carac.spec
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Executable built successfully!" -ForegroundColor Green
        Write-Host "Location: dist/carac.exe" -ForegroundColor Yellow
    } else {
        Write-Host "Build failed!" -ForegroundColor Red
        exit 1
    }
}

function Clean-Build {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Green
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
        Write-Host "Removed dist/ directory" -ForegroundColor Yellow
    }
    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build"
        Write-Host "Removed build/ directory" -ForegroundColor Yellow
    }
    if (Test-Path "*.spec") {
        Remove-Item "*.spec"
        Write-Host "Removed .spec files" -ForegroundColor Yellow
    }
    Write-Host "Clean completed!" -ForegroundColor Green
}

# Main script logic
switch ($Command.ToLower()) {
    "install" { Install-Dependencies }
    "run" { Run-Application }
    "test" { Run-Tests }
    "lint" { Run-Linting }
    "format" { Format-Code }
    "typecheck" { Run-TypeCheck }
    "build" { Build-Executable }
    "clean" { Clean-Build }
    "help" { Show-Help }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\scripts\dev.ps1 help' for usage information" -ForegroundColor Yellow
        exit 1
    }
}

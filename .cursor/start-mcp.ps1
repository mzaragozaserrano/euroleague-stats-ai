#!/usr/bin/env pwsh
# Script wrapper para iniciar el servidor MCP de PostgreSQL
# Lee DATABASE_URL del archivo .env y lo pasa al servidor

param()

# Cargar variables de entorno desde backend/.env
$envFile = Join-Path $PSScriptRoot "backend\.env"

if (Test-Path $envFile) {
    Write-Host "Cargando variables de entorno desde $envFile..." -ForegroundColor Green
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
            if ($key -eq "DATABASE_URL") {
                Write-Host "DATABASE_URL cargada correctamente" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "Advertencia: No se encontr$([char]0x00F3) $envFile" -ForegroundColor Yellow
}

# Si DATABASE_URL está configurada, iniciar el servidor MCP
if ($env:DATABASE_URL) {
    Write-Host "Iniciando servidor MCP de PostgreSQL..." -ForegroundColor Green
    Write-Host "URL: $($env:DATABASE_URL.Substring(0, [Math]::Min(50, $env:DATABASE_URL.Length)))..." -ForegroundColor Cyan
    
    # Ejecutar el servidor MCP
    npx -y "@modelcontextprotocol/server-postgres" $env:DATABASE_URL
} else {
    Write-Host "ERROR: DATABASE_URL no est$([char]0x00E1) configurada" -ForegroundColor Red
    Write-Host "Por favor, configura DATABASE_URL en backend/.env" -ForegroundColor Yellow
    exit 1
}


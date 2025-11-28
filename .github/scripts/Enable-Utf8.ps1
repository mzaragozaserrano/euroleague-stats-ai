# Configuración Centralizada de UTF-8 para GitHub CLI y PowerShell
# Referencia: .github/docs/WINDOWS_UTF8_SETUP.md

Write-Host "Configurando entorno UTF-8..." -ForegroundColor Cyan

chcp 65001 | Out-Null
[Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Retorna el objeto encoding para usar en escritura de archivos
return New-Object System.Text.UTF8Encoding $false
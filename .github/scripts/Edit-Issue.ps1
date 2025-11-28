param([string]$IssueNumber)

if (-not $IssueNumber) {
    $IssueNumber = Read-Host "Introduce el número de Issue a editar (ej: 40)"
}

# 1. Cargar configuración UTF-8
$utf8NoBom = . "$PSScriptRoot\Enable-Utf8.ps1"

# 2. Obtener body actual
Write-Host "Obteniendo contenido de issue #$IssueNumber..." -ForegroundColor Cyan
try {
    $currentBody = gh issue view $IssueNumber --json body | ConvertFrom-Json | Select-Object -ExpandProperty body
}
catch {
    Write-Error "No se pudo encontrar la issue #$IssueNumber"
    exit
}

# ------------------------------------------------------------------
# MODIFICACIONES (EDITA AQUÍ TU LÓGICA DE REEMPLAZO)
# ------------------------------------------------------------------
# Ejemplo: Actualizar dependencias
$newBody = $currentBody -replace '\*\*Dependencias:\*\*.*', "**Dependencias:** #17"
$newBody = $newBody -replace '\*\*Bloquea a:\*\*.*', "**Bloquea a:** #19"

# O reemplazar todo el contenido:
# $newBody = @"
# ... contenido nuevo ...
# "@
# ------------------------------------------------------------------

# 3. Guardar y actualizar
$tempFile = [System.IO.Path]::GetTempFileName()
try {
    [System.IO.File]::WriteAllText($tempFile, $newBody, $utf8NoBom)
    gh issue edit $IssueNumber --body-file $tempFile
    Write-Host "✓ Issue #$IssueNumber actualizada correctamente" -ForegroundColor Green
}
finally {
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}
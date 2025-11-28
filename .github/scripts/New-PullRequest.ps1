# Script para crear Pull Requests con UTF-8 seguro
# Uso: Edita las variables de CONFIGURACIÓN y ejecuta el script.

# ------------------------------------------------------------------
# CONFIGURACIÓN DE LA PR (EDITA ESTO)
# ------------------------------------------------------------------
$Title = "feat: Título con tildes o $([char]0x00F1)" # Usa Unicode si es necesario
$IssueNumber = "40" # Número de la issue que cierra (sin #)

$Body = @"
## Descripci$([char]0x00F3)n
Explicación detallada de los cambios...

## Tipo de Cambio
- [ ] Nueva funcionalidad
- [ ] Correcci$([char]0x00F3)n de errores

Closes #$IssueNumber
"@
# ------------------------------------------------------------------

# 1. Cargar configuración UTF-8
try {
    $utf8NoBom = . "$PSScriptRoot\Enable-Utf8.ps1"
} catch {
    Write-Warning "No se encontró Enable-Utf8.ps1, usando default."
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
}

# 2. Detectar rama actual
$CurrentBranch = git branch --show-current
if (-not $CurrentBranch) { Write-Error "No estás en una rama git."; exit }

# 3. Crear archivo temporal para el cuerpo
$tempFile = [System.IO.Path]::GetTempFileName()
try {
    [System.IO.File]::WriteAllText($tempFile, $Body, $utf8NoBom)
    
    # 4. Crear PR
    Write-Host "Creando PR desde '$CurrentBranch' -> 'main'..." -ForegroundColor Cyan
    gh pr create --title $Title --body-file $tempFile --base main --head $CurrentBranch
}
finally {
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}
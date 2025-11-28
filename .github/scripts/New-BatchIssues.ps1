<#
.SYNOPSIS
    Crea issues en GitHub en lote basándose en una lista definida.
    Este script es modificado automáticamente por el Agente de Cursor antes de su ejecución.
#>

# 1. CARGA LA CONFIGURACIÓN UTF-8 (Para que veas bien los logs)
# $PSScriptRoot es la carpeta donde está este script.
# Si el fichero Enable-Utf8.ps1 no existe, ignoramos el error para no romper nada.
if (Test-Path "$PSScriptRoot/Enable-Utf8.ps1") {
    . "$PSScriptRoot/Enable-Utf8.ps1"
}

# --- ZONA EDITABLE POR EL AGENTE ---
# El agente rellenará este array basándose en el Roadmap.
# IMPORTANTE AGENTE: 
# 1. Usa codificación Hex para caracteres especiales. Ej: "Configuraci$([char]0x00F3)n"
# 2. Consulta .github/docs/labels_convention.md para asignar labels correctamente.
#    Formato: "tipo,tecnologia,fase-X" (ej: "task,backend,fase-2")
$issues = @(
    @{ 
        Title = "Ejemplo: Tarea Inicial"; 
        Body = "Esta es una tarea de prueba. Borrala."; 
        Labels = "documentation,setup" 
    }
)
# -----------------------------------

Write-Host "`n[Iniciando creaci$([char]0x00F3)n de lote de issues...]" -ForegroundColor Cyan

# Verificación de seguridad básica
if ($issues.Count -eq 0) {
    Write-Warning "La lista de issues está vacía. No hay nada que crear."
    exit
}

foreach ($issue in $issues) {
    # Mostramos en pantalla el título
    Write-Host "Creando: $($issue.Title)..." -NoNewline
    
    # Ejecutamos el comando de GitHub CLI
    $result = gh issue create --title $issue.Title --body $issue.Body --label $issue.Labels 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " ERROR" -ForegroundColor Red
        Write-Host $result -ForegroundColor Yellow
    }
    
    # Pequeña pausa de 500ms
    Start-Sleep -Milliseconds 500 
}

Write-Host "`n[Proceso finalizado.]" -ForegroundColor Cyan

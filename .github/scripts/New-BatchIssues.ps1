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
# IMPORTANTE AGENTE: Usa codificación Hex para caracteres especiales. 
# Ej: "Configuraci$([char]0x00F3)n"
$issues = @(
    @{ 
        Title = "Ejemplo: Tarea Inicial"; 
        Body = "Esta es una tarea de prueba. B$([char]0x00F3)rrala."; 
        Labels = "documentation, setup" 
    }
)
# -----------------------------------

Write-Host "`n🚀 Iniciando creación de lote de issues..." -ForegroundColor Cyan

# Verificación de seguridad básica
if ($issues.Count -eq 0) {
    Write-Warning "La lista de issues está vacía. No hay nada que crear."
    exit
}

foreach ($issue in $issues) {
    # Mostramos en pantalla el título (aquí es donde Enable-Utf8 ayuda a que se vea bien)
    Write-Host "Creando: $($issue.Title)..." -NoNewline
    
    # Ejecutamos el comando de GitHub CLI
    # Usamos splatting o argumentos directos. Redirigimos stderr a stdout (2>&1) para capturar errores.
    $result = gh issue create --title $issue.Title --body $issue.Body --label $issue.Labels 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅ OK" -ForegroundColor Green
    } else {
        Write-Host " ❌ ERROR" -ForegroundColor Red
        # Mostramos el error devuelto por gh cli
        Write-Host $result -ForegroundColor Yellow
    }
    
    # Pequeña pausa de 500ms para respetar la API de GitHub y evitar bloqueos por spam
    Start-Sleep -Milliseconds 500 
}

Write-Host "`n✨ Proceso finalizado." -ForegroundColor Cyan
# ------------------------------------------------------------------
# CONFIGURACIÓN DE LA ISSUE (EDITA ESTO)
# ------------------------------------------------------------------
$Title = "[FASE 1.X] Título de la Tarea"

# Usar sintaxis Unicode para caracteres especiales: $([char]0x00F3) = ó
$Body = @"
## $([char]0x00D3)rden de Ejecuci$([char]0x00F3)n

**Tarea:** 1.X
**Dependencias:** Por determinar
**Bloquea a:** Por determinar

---

## Prop$([char]0x00F3)sito
Descripción aquí...

## Contexto y Referencias
* **Fase del Proyecto:** Fase 1
* **Documentaci$([char]0x00F3)n Base:** [03_IMPLEMENTATION_ROADMAP.md](../../docs/03_IMPLEMENTATION_ROADMAP.md)

## Especificaciones
* ...
"@
# ------------------------------------------------------------------

# 1. Cargar configuración UTF-8
$utf8NoBom = . "$PSScriptRoot\Enable-Utf8.ps1"

# 2. Crear archivo temporal
$tempFile = [System.IO.Path]::GetTempFileName()
try {
    [System.IO.File]::WriteAllText($tempFile, $Body, $utf8NoBom)
    
    # 3. Ejecutar comando GH
    Write-Host "Creando issue: $Title" -ForegroundColor Yellow
    gh issue create --title $Title --body-file $tempFile
}
finally {
    # 4. Limpieza
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}
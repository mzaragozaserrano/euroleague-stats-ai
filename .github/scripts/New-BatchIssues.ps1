# 1. Cargar configuración UTF-8
$utf8NoBom = . "$PSScriptRoot\Enable-Utf8.ps1"

# ------------------------------------------------------------------
# 2. FUNCIÓN PLANTILLA (Actualizada a Estándar Profesional)
# ------------------------------------------------------------------
function Get-IssueBody {
    param(
        [string]$TaskNum,
        [string]$Purpose,
        [string]$Specs,
        [string]$ContextDocs = "[03_IMPLEMENTATION_ROADMAP.md](../../docs/03_IMPLEMENTATION_ROADMAP.md)"
    )

    # Unicode: Ó=0xD3, ó=0xF3, é=0xE9, í=0xED
    return @"
## 📋 Metadata

**ID Tarea:** $TaskNum
**Dependencias:** Por determinar
**Bloquea a:** Por determinar

---

## 🎯 Objetivo
$Purpose

## 🔗 Contexto
* **Fase:** $TaskNum (Inferida)
* **Documentaci$([char]0x00F3)n:** $ContextDocs

## 🛠️ Especificaciones T$([char]0x00E9)cnicas
$Specs

## ✅ Definition of Done (DoD)
- [ ] C$([char]0x00F3)digo implementado y funcional
- [ ] Tests unitarios/integraci$([char]0x00F3)n pasando
- [ ] Linter sin errores
- [ ] Relaciones de datos verificadas (Dexie)
"@
}

# ------------------------------------------------------------------
# 3. DEFINICIÓN DE TAREAS
# ------------------------------------------------------------------
$tasks = @(
    @{ 
        TaskNum = "1.1"
        Title   = "feat(setup): inicialización del proyecto"
        Purpose = "Configurar el repositorio base con las herramientas de calidad."
        Specs   = "- Instalar Vite y React`n- Configurar ESLint y Prettier"
    },
    @{ 
        TaskNum = "1.2"
        Title   = "feat(db): configuración de Dexie"
        Purpose = "Establecer la capa de persistencia local."
        Specs   = "- Definir esquema de base de datos`n- Crear servicio de conexión"
    }
)
# ------------------------------------------------------------------

$issueMap = @{}

# Paso 4: Ejecución
foreach ($task in $tasks) {
    $bodyContent = Get-IssueBody -TaskNum $task.TaskNum -Purpose $task.Purpose -Specs $task.Specs
    $bodyFinal = $bodyContent + "`n`n> **Nota:** Referencias autom$([char]0x00E1)ticas pendientes."
    
    $tempFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tempFile, $bodyFinal, $utf8NoBom)
    
    try {
        Write-Host "Creando: $($task.Title)..." -NoNewline
        $result = gh issue create --title $task.Title --body-file $tempFile
        
        if ($result -match 'issues/(\d+)') {
            $num = $matches[1]
            $issueMap[$task.TaskNum] = $num
            Write-Host " -> OK (#$num)" -ForegroundColor Green
        }
    }
    finally {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 500
}

Write-Host "`n--- MAPA DE ISSUES ---" -ForegroundColor Yellow
$issueMap.Keys | Sort-Object | ForEach-Object { "$_ = #$($issueMap[$_])" }
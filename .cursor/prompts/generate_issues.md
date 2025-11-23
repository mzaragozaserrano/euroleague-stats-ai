# Ejecutor de Issues (Windows Safe Mode)

Actúa como un **Project Manager Autónomo**.
Tu misión es crear los tickets en GitHub para las tareas pendientes.

## Proceso
1.  **Lee** el documento de estado (ej. `FASE_1_EN_PROGRESO.md`).
2.  **Identifica** las tareas pendientes.
3.  **Lee** la plantilla `.github/ISSUE_TEMPLATE/implementation_task.md`.
4.  **EJECUTA** la secuencia de comandos segura definida abajo.

## Protocolo OBLIGATORIO Anti-Mojibake (Windows)
En Windows, pasar texto con tildes directamente a `gh` rompe la codificación.
**Debes seguir ESTRICTAMENTE este procedimiento para CADA issue:**

### Paso 1: Configurar la Sesión (Ejecutar una sola vez al inicio)
Antes de crear nada, ejecuta estos comandos para forzar UTF-8 en la consola actual:
```powershell
chcp 65001 | Out-Null
[Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

### Paso 2: Crear el Issue (Método de Archivos Temporales para TODO)
Para CADA tarea, usa archivos temporales tanto para el título como para el body:

1.  **Crea archivo temporal para el título** (sin BOM):
    ```powershell
    $titleContent = "[Fase 1] Diseño del Esquema de Base de Datos"
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText("temp_title.txt", $titleContent, $utf8NoBom)
    ```

2.  **Crea archivo temporal para el body** (sin BOM):
    ```powershell
    $bodyContent = @"
## Propósito
Crear el esquema inicial de la base de datos...
"@
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText("temp_body.md", $bodyContent, $utf8NoBom)
    ```

3.  **Lee el título usando ReadAllBytes (sin BOM) y ejecuta el comando `gh`**:
    ```powershell
    $titleBytes = [System.IO.File]::ReadAllBytes("temp_title.txt")
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $title = $utf8NoBom.GetString($titleBytes).Trim()
    gh issue create --title $title --body-file "temp_body.md" --label "backend,fase-1"
    ```

4.  **Borra los archivos temporales**:
    ```powershell
    Remove-Item "temp_title.txt", "temp_body.md" -ErrorAction SilentlyContinue
    ```

### Alternativa 1: Método con Variable de Entorno
Si el método anterior aún muestra caracteres incorrectos, usa variables de entorno:

```powershell
# Leer título con ReadAllBytes (sin BOM)
$titleBytes = [System.IO.File]::ReadAllBytes("temp_title.txt")
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$title = $utf8NoBom.GetString($titleBytes).Trim()

# Guardar en variable de entorno y usar
$env:GH_ISSUE_TITLE = $title
gh issue create --title $env:GH_ISSUE_TITLE --body-file "temp_body.md" --label "backend,fase-1"
Remove-Item Env:\GH_ISSUE_TITLE
```

### Alternativa 2: Usar `gh api` con JSON (MÁS ROBUSTO - RECOMENDADO)
Si los métodos anteriores fallan, usa la API de GitHub directamente con JSON. Este método evita problemas de codificación:

```powershell
# Función helper para leer archivos UTF-8 sin BOM
function Read-Utf8File {
    param([string]$Path)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    return $utf8NoBom.GetString($bytes)
}

# Leer título y body desde archivos
$title = (Read-Utf8File "temp_title.txt").Trim()
$body = Read-Utf8File "temp_body.md"

# IMPORTANTE: Si creas los strings directamente en PowerShell con caracteres especiales,
# usa códigos Unicode para evitar problemas de codificación:
# $title = "[Fase 1.1] Dise" + [char]0x00F1 + "o del Esquema"  # ñ = 0x00F1
# $body = "## Prop" + [char]0x00F3 + "sito`n`n..."  # ó = 0x00F3

# Obtener información del repositorio
$repoInfo = gh repo view --json owner,name | ConvertFrom-Json
$repoPath = "$($repoInfo.owner.login)/$($repoInfo.name)"

# Crear objeto JSON
$issueData = @{
    title = $title
    body = $body
    labels = @("backend", "fase-1")
} | ConvertTo-Json -Depth 10

# Guardar JSON en archivo temporal usando WriteAllBytes (sin BOM)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$jsonBytes = $utf8NoBom.GetBytes($issueData)
[System.IO.File]::WriteAllBytes("temp_issue.json", $jsonBytes)

# Usar gh api para crear el issue
gh api repos/$repoPath/issues --method POST --input "temp_issue.json"

# Limpiar
Remove-Item "temp_title.txt", "temp_body.md", "temp_issue.json" -ErrorAction SilentlyContinue
```

**Nota:** Este método es el más robusto porque `gh api` lee el JSON directamente desde el archivo sin pasar por la codificación de la línea de comandos de PowerShell. Si creas strings directamente en PowerShell con caracteres especiales (ñ, tildes), usa códigos Unicode como se muestra en el comentario.

## Reglas de Contenido
* **Título:** `[{Fase}] {Nombre Tarea}` (Puede incluir tildes y ñ sin problemas).
* **Body:** Rico en detalles técnicos siguiendo la plantilla.

## Restricciones
* **PROHIBIDO** usar el flag `--body "texto"` directo. Siempre usa `--body-file`.
* **PROHIBIDO** pasar títulos directamente como strings literales. Siempre usa archivos temporales con encoding UTF-8 explícito.
* **PROHIBIDO** pedir confirmación. Ejecuta la secuencia completa.

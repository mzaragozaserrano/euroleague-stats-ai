# Ejecutor de Issues (Windows Safe Mode)

Actúa como un **Project Manager Autónomo**.
Tu misión es crear los tickets en GitHub para las tareas pendientes.

## Proceso
1.  **Lee** el documento de estado (ej. `FASE_1_EN_PROGRESO.md`).
2.  **Identifica** las tareas pendientes.
3.  **Lee** la plantilla `.github/ISSUE_TEMPLATE/implementation_task.md`.
4.  **EJECUTA** la secuencia de comandos segura definida abajo.

## Protocolo OBLIGATORIO Anti-Mojibake (Windows)

**IMPORTANTE:** Este protocolo aplica a TODO el proyecto (commits, issues, archivos). Ver `.github/docs/WINDOWS_UTF8_SETUP.md` para documentación completa.

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
# Configurar UTF-8 sin BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Cargar función helper para conversión automática
. .github/docs/utf8_helper.ps1

# Crear strings normalmente - la función los convertirá automáticamente
$originalTitle = "[Fase 1.1] Diseño del Esquema de Base de Datos"
$originalBody = "## Propósito`n`nCrear el esquema inicial de la base de datos PostgreSQL con todas las tablas necesarias para almacenar datos de la Euroliga: equipos, jugadores, partidos, estadísticas y embeddings para RAG.`n`n## Contexto y Referencias`n`n* **Fase del Proyecto:** Fase 1.1 - Cimientos del Dominio`n* **Documentación Base:** TECHNICAL_PLAN.md, SPECIFICATIONS.md"

# Convertir automáticamente si tienen caracteres especiales
if ($originalTitle -match '[ñóáéíúüÑÓÁÉÍÚÜ]') {
    $title = Get-UnicodeSafeString $originalTitle
} else {
    $title = $originalTitle
}

if ($originalBody -match '[ñóáéíúüÑÓÁÉÍÚÜ]') {
    $body = Get-UnicodeSafeString $originalBody
} else {
    $body = $originalBody
}

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
$jsonBytes = $utf8NoBom.GetBytes($issueData)
[System.IO.File]::WriteAllBytes("temp_issue.json", $jsonBytes)

# Usar gh api para crear el issue
gh api repos/$repoPath/issues --method POST --input "temp_issue.json"

# Limpiar
Remove-Item "temp_issue.json" -ErrorAction SilentlyContinue
```

**Nota:** Este método es el más robusto porque `gh api` lee el JSON directamente desde el archivo sin pasar por la codificación de la línea de comandos de PowerShell. **RECOMENDADO:** Usar la función `Get-UnicodeSafeString` del helper (`.github/docs/utf8_helper.ps1`) para conversión automática de caracteres especiales.

## Conversión Automática de Caracteres Especiales

**RECOMENDADO:** Usar la función helper automática (ver `.github/docs/WINDOWS_UTF8_SETUP.md`):

```powershell
# Cargar función helper
. .github/docs/utf8_helper.ps1

# Crear strings normalmente - se convierten automáticamente
$originalMsg = "Añadir documentación"
if ($originalMsg -match '[ñóáéíúüÑÓÁÉÍÚÜ]') {
    $msg = Get-UnicodeSafeString $originalMsg
} else {
    $msg = $originalMsg
}
```

**Nota:** Para métodos manuales o referencia completa de códigos Unicode, ver `.github/docs/WINDOWS_UTF8_SETUP.md`.

## Reglas de Contenido
* **Título:** `[{Fase}] {Nombre Tarea}` (Puede incluir tildes y ñ sin problemas).
* **Body:** Rico en detalles técnicos siguiendo la plantilla.

## Restricciones
* **PROHIBIDO** usar el flag `--body "texto"` directo. Siempre usa `--body-file`.
* **PROHIBIDO** pasar títulos directamente como strings literales. Siempre usa archivos temporales con encoding UTF-8 explícito.
* **PROHIBIDO** pedir confirmación. Ejecuta la secuencia completa.

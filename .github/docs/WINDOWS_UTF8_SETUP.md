# Configuración UTF-8 para Windows

## Problema

En Windows, PowerShell y Git pueden tener problemas con la codificación UTF-8 cuando se manejan caracteres especiales (tildes, ñ, etc.). Esto afecta a:
- **Commits de Git**: Los mensajes con caracteres especiales pueden aparecer mal codificados
- **Issues de GitHub**: Los títulos y descripciones con tildes/ñ pueden mostrar caracteres extraños (mojibake)
- **Archivos de texto**: La lectura/escritura de archivos con caracteres especiales

## Solución: Configuración de Sesión PowerShell

Antes de ejecutar cualquier comando que involucre caracteres especiales, configura la sesión de PowerShell:

```powershell
# Configurar página de códigos a UTF-8
chcp 65001 | Out-Null

# Configurar encoding de entrada y salida
[Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

## Método Recomendado: Códigos Unicode para Strings en PowerShell

Cuando crees strings directamente en PowerShell con caracteres especiales, **usa códigos Unicode** para evitar problemas de codificación:

### Códigos Unicode Comunes para Caracteres Españoles

| Carácter | Código Unicode | Ejemplo PowerShell |
|----------|----------------|---------------------|
| `ñ` | `0x00F1` | `"Dise" + [char]0x00F1 + "o"` → `"Diseño"` |
| `ó` | `0x00F3` | `"Prop" + [char]0x00F3 + "sito"` → `"Propósito"` |
| `á` | `0x00E1` | `"est" + [char]0x00E1 + " creado"` → `"está creado"` |
| `é` | `0x00E9` | `"m" + [char]0x00E9 + "todo"` → `"método"` |
| `í` | `0x00ED` | `"estad" + [char]0x00ED + "sticas"` → `"estadísticas"` |
| `ú` | `0x00FA` | `"b" + [char]0x00FA + "squeda"` → `"búsqueda"` |
| `ü` | `0x00FC` | `"ling" + [char]0x00FC + "ista"` → `"lingüista"` |
| `Ñ` | `0x00D1` | `"A" + [char]0x00D1 + "O"` → `"AÑO"` |
| `Ó` | `0x00D3` | `"PROP" + [char]0x00D3 + "SITO"` → `"PROPÓSITO"` |

### Ejemplo Completo

```powershell
# Configurar UTF-8
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Crear strings con códigos Unicode
$title = "[Fase 1.1] Dise" + [char]0x00F1 + "o del Esquema"
$body = "## Prop" + [char]0x00F3 + "sito`n`nCrear el esquema inicial con estad" + [char]0x00ED + "sticas."

# Usar en comandos de Git/GitHub
git commit -m $title
```

## Uso en Git Commits

### Método Automático (RECOMENDADO)

Usa la función helper para conversión automática:

```powershell
# Configurar sesión UTF-8
chcp 65001 | Out-Null
[Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Cargar función helper
. .github/docs/utf8_helper.ps1

# Convertir mensaje automáticamente si tiene caracteres especiales
$originalMsg = "Añadiendo documentación"
if ($originalMsg -match '[ñóáéíúüÑÓÁÉÍÚÜ]') {
    $msg = Get-UnicodeSafeString $originalMsg
} else {
    $msg = $originalMsg
}
git commit -m $msg
```

### Método Manual (Alternativa)

Si prefieres hacerlo manualmente:

```powershell
# Configurar sesión UTF-8 (ver arriba)
chcp 65001 | Out-Null
[Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Crear mensaje con códigos Unicode manualmente
$message = "A" + [char]0x00F1 + "adiendo documentaci" + [char]0x00F3 + "n"
git commit -m $message
```

## Uso en GitHub Issues

Para crear issues con caracteres especiales, usar `gh api` con JSON y códigos Unicode:

```powershell
# Configurar UTF-8 sin BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Crear título y body con códigos Unicode
$title = "[Fase 1.1] Dise" + [char]0x00F1 + "o del Esquema"
$body = "## Prop" + [char]0x00F3 + "sito`n`n..."

# Crear JSON
$issueData = @{
    title = $title
    body = $body
} | ConvertTo-Json -Depth 10

# Guardar JSON con UTF-8 sin BOM
$jsonBytes = $utf8NoBom.GetBytes($issueData)
[System.IO.File]::WriteAllBytes("temp_issue.json", $jsonBytes)

# Crear issue usando gh api
$repoInfo = gh repo view --json owner,name | ConvertFrom-Json
$repoPath = "$($repoInfo.owner.login)/$($repoInfo.name)"
gh api repos/$repoPath/issues --method POST --input "temp_issue.json"
```

## Lectura/Escritura de Archivos

Para leer/escribir archivos con caracteres especiales:

```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Escribir archivo
$content = "Contenido con tildes y " + [char]0x00F1
[System.IO.File]::WriteAllText("archivo.txt", $content, $utf8NoBom)

# Leer archivo
$bytes = [System.IO.File]::ReadAllBytes("archivo.txt")
$content = $utf8NoBom.GetString($bytes)
```

## Función Helper Automática

Para facilitar la conversión automática, se proporciona una función helper en `.github/docs/utf8_helper.ps1`:

```powershell
# Cargar la función
. .github/docs/utf8_helper.ps1

# Usar la función para convertir automáticamente
$safeString = Get-UnicodeSafeString "Añadir documentación"
# Resultado: String con ñ y ó convertidos a códigos Unicode internamente
```

Esta función detecta automáticamente caracteres especiales y los convierte, evitando tener que hacerlo manualmente.

## Referencias

- Ver `.cursor/prompts/generate_issues.md` para ejemplos específicos de creación de issues
- Ver `.cursorrules` para reglas generales del proyecto
- Ver `.github/docs/utf8_helper.ps1` para la función helper de conversión automática


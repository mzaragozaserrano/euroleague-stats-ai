# Referencia UTF-8 y Unicode para Windows

Este documento es la fuente de verdad para el manejo de caracteres especiales en PowerShell.

## 1. Configuración del Entorno (Automática)

No ejecutes comandos manuales. La configuración de `chcp 65001` y codificación de consola está centralizada en:

```powershell
.github/scripts/Enable-Utf8.ps1
```

## 2. Reglas de Sintaxis según el Contexto

### A. Mensajes de Commit (git commit -m)

**CRÍTICO:** Git en Windows puede corromper caracteres especiales. Usa obligatoriamente subexpresiones:

```powershell
# ✅ Correcto
git commit -m "feat: validaci$([char]0x00F3)n de l$([char]0x00F3)gica"

# ❌ Incorrecto - Puede fallar
git commit -m "feat: validación de lógica"
```

### B. Issues y PRs (gh cli) - RECOMENDADO: Here-Strings (@"..."@)

**ÓPTIMO:** Usa Here-Strings para títulos y bodies. `gh cli` maneja UTF-8 internamente:

```powershell
# ✅ MEJOR OPCIÓN: Here-String para todo
$issue = @{
    Title = @"2.1 Vectorización: Script para generar embeddings"@
    Body = @"
Crear el servicio basándose en la consulta del usuario.
Diseñar prompt engineering y búsqueda de similaridad.
Validar que las tildes se vean bien en GitHub.
"@
}

gh issue create --title $issue.Title --body $issue.Body

# ✅ También funciona: Tildes directas sin Here-String
Title = "2.1 Vectorización: Script para generar embeddings"

# ❌ Evitar: Subexpresiones para títulos/bodies (verboso e innecesario)
Title = "2.1 Vectorizaci$([char]0x00F3)n: Script para generar embeddings"
```

### C. Variables y Strings cortos (cuando NO uses Here-Strings)

Si no usas Here-Strings, usa subexpresiones para mayor seguridad:

```powershell
# ✅ Recomendado (funciona en todos los casos)
$mensaje = "Configuraci$([char]0x00F3)n b$([char]0x00E1)sica"

# ⚠️ Puede funcionar pero menos seguro
$mensaje = "Configuración básica"
```

## 3. Tabla de Referencia Unicode

| Carácter | Código Unicode | Subexpresión | Uso en Here-String |
|----------|----------------|--------------|-------------------|
| `ñ` | `0x00F1` | `$([char]0x00F1)` | Escribe `ñ` directo |
| `ó` | `0x00F3` | `$([char]0x00F3)` | Escribe `ó` directo |
| `á` | `0x00E1` | `$([char]0x00E1)` | Escribe `á` directo |
| `é` | `0x00E9` | `$([char]0x00E9)` | Escribe `é` directo |
| `í` | `0x00ED` | `$([char]0x00ED)` | Escribe `í` directo |
| `ú` | `0x00FA` | `$([char]0x00FA)` | Escribe `ú` directo |
| `Ñ` | `0x00D1` | `$([char]0x00D1)` | Escribe `Ñ` directo |
| `Ó` | `0x00D3` | `$([char]0x00D3)` | Escribe `Ó` directo |
| `Á` | `0x00C1` | `$([char]0x00C1)` | Escribe `Á` directo |
| `É` | `0x00C9` | `$([char]0x00C9)` | Escribe `É` directo |
| `Í` | `0x00CD` | `$([char]0x00CD)` | Escribe `Í` directo |
| `Ú` | `0x00DA` | `$([char]0x00DA)` | Escribe `Ú` directo |

---

## 4. Matriz de Decisión Rápida

| Situación | Solución Recomendada | Alternativa | Ejemplo |
|-----------|----------------------|-------------|---------|
| **Commit message** | Subexpresión `$([char]0x00XX)` | N/A | `git commit -m "feat: validaci$([char]0x00F3)n"` |
| **Issue título** | Here-String `@"..."@` | Tildes directas OK | `Title = @"Vectorización"@` |
| **Issue body** | Here-String `@"..."@` | Tildes directas OK | `Body = @"Función de búsqueda"@` |
| **Variable corta** | Here-String o Subexpresión | Tildes directas | `$msg = @"Precisión SQL"@` |
| **Consola (Write-Host)** | Tildes directas | Here-String | `Write-Host "Validación ok"` |

---

## 5. Ejemplos Prácticos

### Crear Issue con Tildes Correctas

```powershell
# Cargar UTF-8
. ".github/scripts/Enable-Utf8.ps1"

# Definir issue con Here-String
$issue = @{
    Title = "Función de búsqueda avanzada"
    Body = @"
Implementar búsqueda con análisis semántico.

## Tareas:
- Diseñar algoritmo de similaridad
- Validar con datos reales
- Documentar parámetros

## Criterios de Aceptación:
- Latencia < 500ms
- Cobertura >= 85%
"@
    Labels = "task,backend,fase-2"
}

# Crear
gh issue create --title $issue.Title --body $issue.Body --label $issue.Labels
```

### Commit con Tildes

```powershell
# Obligatorio usar subexpresiones
git commit -m "feat: implementaci$([char]0x00F3)n de b$([char]0x00FAs)queda"
```

### Script de Batch Issues (Recomendado)

Ver `.github/scripts/New-BatchIssues.ps1` - usa Here-Strings y tildes directas en el body.

---

## 6. Workflows & Execution Context

**IMPORTANTE:** El manejo de UTF-8 cambia según quien ejecuta el comando:

| Executor | git commit -m | gh cli | Referencia |
|----------|--------------|--------|-----------|
| **Local PowerShell** | Subexpressions | Here-Strings | `.cursor/workflows/*` |
| **GitHub Actions** | Direct tildes | Direct tildes | CI/CD (future) |

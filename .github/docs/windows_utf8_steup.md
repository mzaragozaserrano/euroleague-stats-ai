# Referencia UTF-8 y Unicode para Windows

Este documento es la fuente de verdad para el manejo de caracteres especiales en PowerShell.

## 1. Configuración del Entorno (Automática)

No ejecutes comandos manuales. La configuración de `chcp 65001` y codificación de consola está centralizada en:

```powershell
.github/scripts/Enable-Utf8.ps1
```

## 2. Regla de Sintaxis para Strings

**CRÍTICO:** Al escribir mensajes de commit o contenido de issues desde PowerShell, **NUNCA** uses caracteres especiales directos (`ñ`, `ó`) ni concatenación `+`.

**Sintaxis Obligatoria:** Usa subexpresiones dentro del string:
✅ Correcto: `"Actualizaci$([char]0x00F3)n"`
❌ Incorrecto: `"Actualización"`

## 3. Tabla de Referencia Unicode

| Carácter | Código Unicode | Uso en PowerShell |
|----------|----------------|-------------------|
| `ñ` | `0x00F1` | `$([char]0x00F1)` |
| `ó` | `0x00F3` | `$([char]0x00F3)` |
| `á` | `0x00E1` | `$([char]0x00E1)` |
| `é` | `0x00E9` | `$([char]0x00E9)` |
| `í` | `0x00ED` | `$([char]0x00ED)` |
| `ú` | `0x00FA` | `$([char]0x00FA)` |
| `Ñ` | `0x00D1` | `$([char]0x00D1)` |
| `Ó` | `0x00D3` | `$([char]0x00D3)` |
| `Á` | `0x00C1` | `$([char]0x00C1)` |
| `É` | `0x00C9` | `$([char]0x00C9)` |
| `Í` | `0x00CD` | `$([char]0x00CD)` |
| `Ú` | `0x00DA` | `$([char]0x00DA)` |

---

## 4. Ejemplos de uso

### En Commit Manual

```powershell
git commit -m "feat: validaci$([char]0x00F3)n de l$([char]0x00F3)gica"
```

### En Script

```powershell
$Titulo = "Configuraci$([char]0x00F3)n b$([char]0x00E1)sica"
```